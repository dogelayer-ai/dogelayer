import argparse
import os
import traceback
import time
import asyncio
import threading
import typing
import copy

import bittensor as bt
from bittensor import logging
from dotenv import load_dotenv

from dogelayer.core.chain_data.pool_info import PoolInfo
from dogelayer.core.pool import PoolIndex
from dogelayer.miner import BaseMiner
from dogelayer.miner.proxy import (
    get_proxy_manager,
    BraiinsProxyManager,
    DogeLayerProxyManager,
)

DEFAULT_SYNC_FREQUENCY = 6


class EnhancedDogeLayerMiner(BaseMiner):
    """
    Enhanced DogeLayer Miner combining proxy mining with axon services.

    This miner supports:
    1. Proxy mining (original dogelayer functionality)
    2. Axon server for validator requests (taoillium functionality)
    3. Business server integration
    4. Weight setting capabilities
    """

    def __init__(self):
        """Initialize the enhanced miner with both proxy and axon capabilities."""
        # Base miner initialization
        super().__init__()

        # Validate addresses (at least one must be provided)
        self.configured_addrs = self._validate_addresses()

        # Proxy manager setup
        self.proxy_manager = None
        if getattr(self.config, 'use_proxy', True):
            try:
                self.proxy_manager = get_proxy_manager(
                    proxy_type=getattr(self.config, 'proxy_type', 'dogelayer'),
                    config=self.config
                )
                logging.info("✅ Proxy manager initialized successfully")
            except Exception as e:
                logging.warning(f"⚠️ Failed to initialize proxy manager: {e}")
                logging.warning("Mining will continue without proxy functionality")

        # Axon setup (from taoillium)
        self.axon = None
        self.should_exit = False
        self.is_running = False
        self.thread = None
        self.lock = asyncio.Lock()

        # Business server integration variables
        self.current_api_key_name = None
        self.current_api_key_value = None
        self.last_neuron_registration_expire = time.time() + 600
        self.last_service_token_expire = time.time() + 600
        self.axon_data = {}

        # Setup axon if enabled
        if getattr(self.config, 'enable_axon', True):
            self._setup_axon()
            self._setup_business_server_integration()

        # Generate and log worker name
        worker_name = self._generate_worker_name()
        logging.info(f"✅ Enhanced DogeLayer Miner initialized successfully")
        logging.info(f"🏷️ Worker Name: {worker_name}")
        logging.info(f"📍 Configured Addresses: {', '.join(self.configured_addrs)}")
        logging.info(f"🆔 Worker ID: {getattr(self, 'worker_id', 'default')}")

    def _validate_addresses(self):
        """Validate and collect configured addresses."""
        btc_addr = getattr(self.config, 'btc_address', None)
        ltc_addr = getattr(self.config, 'ltc_address', None)
        doge_addr = getattr(self.config, 'doge_address', None)

        if not any([btc_addr, ltc_addr, doge_addr]):
            logging.error(
                "❌ Please configure at least one of BTC_ADDRESS / LTC_ADDRESS / DOGE_ADDRESS.")
            exit(1)

        # Soft-validate formats (warnings only)
        def _warn_address(addr, prefixes, label):
            if addr and not addr.startswith(prefixes):
                logging.warning(
                    f"⚠️ {label} address format looks unusual: {addr}")

        _warn_address(ltc_addr, ("L", "M", "ltc1", "rltc1"), "LTC")
        _warn_address(doge_addr, ("D", "A", "doge1", "n", "m", "muk1"), "DOGE")
        _warn_address(btc_addr, ("1", "3", "bc1"), "BTC")

        # Return configured addresses in order: LTC -> DOGE -> BTC
        configured_addrs = [a for a in [ltc_addr, doge_addr, btc_addr] if a]
        logging.info(
            f"Configured addresses: {len(configured_addrs)} ({', '.join(configured_addrs[:2])}...)")

        return configured_addrs

    def _setup_axon(self):
        """Setup axon server for validator requests."""
        logging.info("Setting up axon server...")

        # Security warnings
        if not getattr(self.config.blacklist, 'force_validator_permit', True):
            logging.warning(
                "You are allowing non-validators to send requests to your miner. This is a security risk."
            )
        if getattr(self.config.blacklist, 'allow_non_registered', False):
            logging.warning(
                "You are allowing non-registered entities to send requests to your miner. This is a security risk."
            )

        # Create axon
        config_to_use = self.config() if callable(self.config) else self.config
        logging.info(f"🔍 Creating axon with config.axon: {getattr(config_to_use, 'axon', 'NOT_FOUND')}")
        if hasattr(config_to_use, 'axon'):
            logging.info(f"  axon.ip: {getattr(config_to_use.axon, 'ip', 'NOT_SET')}")
            logging.info(f"  axon.port: {getattr(config_to_use.axon, 'port', 'NOT_SET')}")

        self.axon = bt.axon(
            wallet=self.wallet,
            config=config_to_use,
        )

        # Attach handlers
        logging.info("Attaching forward function to miner axon.")
        self.axon.attach(
            forward_fn=self.forward,
            blacklist_fn=self.blacklist,
            priority_fn=self.priority,
        )
        logging.info(f"Axon created: {self.axon}")

    def _setup_business_server_integration(self):
        """Setup business server integration."""
        logging.info("Setting up business server integration...")

        # Setup API key
        my_srv_api_key = f"SRV_API_KEY_{self.wallet.hotkey.ss58_address}"

        if os.getenv(my_srv_api_key):
            self.current_api_key_value = os.getenv(my_srv_api_key)
            self.current_api_key_name = my_srv_api_key
            logging.info(f"Using SRV_API_KEY from environment variable: {my_srv_api_key}")
        elif os.getenv("SRV_API_KEY"):
            self.current_api_key_value = os.getenv("SRV_API_KEY")
            self.current_api_key_name = "SRV_API_KEY"
            logging.info("Using SRV_API_KEY from environment variable: SRV_API_KEY")
        else:
            logging.warning("No SRV_API_KEY found, business server integration may be limited")

    async def forward(self, synapse: bt.Synapse) -> bt.Synapse:
        """
        Forward function for handling validator requests.
        This is called when validators send requests to this miner.
        """
        logging.debug(f"Miner forward synapse input: {getattr(synapse, 'input', 'No input')}")

        try:
            # Handle different types of requests
            if hasattr(synapse, 'input') and isinstance(synapse.input, dict):
                request_type = synapse.input.get("__type__")

                if request_type == "health":
                    logging.info(f"Miner health check: {synapse.input}")
                    synapse.output = {
                        "method": "health",
                        "success": True,
                        "uid": self.uid,
                        "device": getattr(self.config.neuron, 'device', 'cpu'),
                        "proxy_status": "active" if self.proxy_manager else "inactive",
                        "addresses": self.configured_addrs
                    }
                elif request_type == "ping":
                    logging.info(f"Miner ping: {synapse.input}")
                    synapse.output = {
                        "method": "ping",
                        "success": True,
                        "uid": self.uid,
                        "timestamp": time.time()
                    }
                else:
                    # Handle business server API requests (taoillium style)
                    try:
                        if self.current_api_key_value:
                            response = self.api_post("/sapi/node/task/create", synapse.input)
                            synapse.output = response
                        else:
                            synapse.output = {
                                "method": "taskCreate",
                                "success": False,
                                "uid": self.uid,
                                "error": "No API key available for business server"
                            }
                    except Exception as api_error:
                        logging.error(f"Business server API error: {api_error}")
                        synapse.output = {
                            "method": "taskCreate",
                            "success": False,
                            "uid": self.uid,
                            "error": str(api_error)
                        }
            else:
                synapse.output = {
                    "method": "error",
                    "success": False,
                    "uid": self.uid,
                    "error": "Invalid synapse input format"
                }

        except Exception as e:
            logging.error(f"Miner forward error: {e}")
            synapse.output = {
                "method": "error",
                "success": False,
                "uid": self.uid,
                "error": str(e)
            }

        logging.info(f"Miner forward response: {synapse.output}")
        return synapse

    def api_post(self, endpoint: str, data: dict) -> dict:
        """
        Make POST request to business server API (taoillium style).
        """
        try:
            import requests

            if not self.current_api_key_value:
                return {"error": "No API key available"}

            base_url = os.getenv("SRV_API_URL", "https://api.taoillium.ai")
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

            headers = {
                "Authorization": f"Bearer {self.current_api_key_value}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logging.error(f"API POST error: {e}")
            return {"error": str(e)}

    async def blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
        """
        Blacklist function to filter incoming requests.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            logging.warning("Received a request without a dendrite or hotkey.")
            return True, "Missing dendrite or hotkey"

        # Check if hotkey is registered
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            if not getattr(self.config.blacklist, 'allow_non_registered', False):
                logging.trace(f"Blacklisting un-registered hotkey {synapse.dendrite.hotkey}")
                return True, "Unrecognized hotkey"

        # Check validator permit
        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if getattr(self.config.blacklist, 'force_validator_permit', True):
            if not self.metagraph.validator_permit[uid]:
                logging.warning(f"Blacklisting non-validator hotkey {synapse.dendrite.hotkey}")
                return True, "Non-validator hotkey"

        logging.trace(f"Not blacklisting recognized hotkey {synapse.dendrite.hotkey}")
        return False, "Hotkey recognized!"

    async def priority(self, synapse: bt.Synapse) -> float:
        """
        Priority function to determine request processing order.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            logging.warning("Received a request without a dendrite or hotkey.")
            return 0.0

        try:
            caller_uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            priority = float(self.metagraph.S[caller_uid])  # Use stake as priority
            logging.trace(f"Prioritizing {synapse.dendrite.hotkey} with value: {priority}")
            return priority
        except (ValueError, IndexError):
            logging.warning(f"Could not find UID for hotkey {synapse.dendrite.hotkey}")
            return 0.0

    def add_args(self, parser: argparse.ArgumentParser):
        """Add enhanced miner arguments to the parser."""
        super().add_args(parser)

        # 添加 axon 参数 (这很重要！)
        bt.axon.add_args(parser)

        # Subtensor network configuration - 添加对SUBTENSOR_NETWORK环境变量的支持
        parser.add_argument(
            "--subtensor.chain_endpoint",
            type=str,
            default=os.getenv("SUBTENSOR_NETWORK", "ws://127.0.0.1:9944"),
            help="Subtensor chain endpoint URL",
        )

        
        parser.add_argument(
            "--btc_address",
            type=str,
            default=os.getenv("BTC_ADDRESS"),
            help="Bitcoin address for receiving mining rewards (optional)",
        )
        parser.add_argument(
            "--ltc_address",
            type=str,
            default=os.getenv("LTC_ADDRESS"),
            help="Litecoin address (optional; primary in merged LTC-DOGE)",
        )
        parser.add_argument(
            "--doge_address",
            type=str,
            default=os.getenv("DOGE_ADDRESS"),
            help="Dogecoin address (optional; auxiliary in merged LTC-DOGE)",
        )
        parser.add_argument(
            "--proxy_type",
            type=str,
            choices=["dogelayer", "braiins"],
            default=os.getenv("PROXY_TYPE", "dogelayer"),
            help="Proxy type to use (dogelayer or braiins)",
        )
        parser.add_argument(
            "--use_proxy",
            action="store_true",
            default=os.getenv("USE_PROXY", "true").lower() == "true",
            help="Enable proxy mining functionality",
        )

        # Enhanced miner arguments
        parser.add_argument(
            "--enable_axon",
            action="store_true",
            default=os.getenv("ENABLE_AXON", "true").lower() == "true",
            help="Enable axon server for validator requests",
        )
        parser.add_argument(
            "--enable_weight_setting",
            action="store_true",
            default=os.getenv("ENABLE_WEIGHT_SETTING", "false").lower() == "true",
            help="Enable periodic weight setting on chain",
        )

        # Blacklist arguments
        parser.add_argument(
            "--blacklist.force_validator_permit",
            action="store_true",
            default=True,
            help="Only allow requests from validators",
        )
        parser.add_argument(
            "--blacklist.allow_non_registered",
            action="store_true",
            default=False,
            help="Allow requests from non-registered entities",
        )

        # Add proxy-specific arguments based on type
        args, _ = parser.parse_known_args()
        if hasattr(args, "proxy_type"):
            if args.proxy_type == "dogelayer":
                DogeLayerProxyManager.add_args(parser)
            elif args.proxy_type == "braiins":
                BraiinsProxyManager.add_args(parser)

    def get_target_pool(self) -> dict[str, PoolInfo]:
        """
        Fetch the subnet's pool from the chain.

        Returns:
            Dict: Dictionary containing only the subnet's pool information

        Process:
            1. Get the subnet's pool info
            2. Verify it's a Proxy pool
            3. Enhance pool data with worker-specific username
        """
        subnet_pool_info = self.get_subnet_pool()
        if not subnet_pool_info:
            logging.warning("Subnet's pool has not published information - this is normal for local testing")
            logging.info("Mining will continue with axon-only functionality (taoillium mode)")
            return {}

        if subnet_pool_info.pool_index != PoolIndex.Proxy:
            logging.error(
                f"Subnet's pool is not a Proxy pool (index: {subnet_pool_info.pool_index}). "
                f"Expected PoolIndex.Proxy ({PoolIndex.Proxy})"
            )
            return {}

        subnet_pool_info.extra_data["full_username"] = self._generate_worker_name()

        return {self.pool_hotkey: subnet_pool_info.to_json()}

    def _generate_worker_name(self):
        """Generate worker name from configured addresses."""
        # Generate worker suffix from hotkey (first 4 + last 4 characters)
        if self.wallet and self.wallet.hotkey:
            hotkey = self.wallet.hotkey.ss58_address
            worker_suffix = hotkey[:4] + hotkey[-4:]
        else:
            worker_suffix = 'default'
        
        # Store worker_id for later use
        self.worker_id = worker_suffix
        
        # Build worker name by concatenating all configured addresses with '-'
        # Example: ltcAddr-dogeAddr-btcAddr.rigID (order as above)
        if self.configured_addrs:
            worker_name = f"{'-'.join(self.configured_addrs)}.{worker_suffix}"
        else:
            worker_name = f"no-address.{worker_suffix}"
            
        logging.info(f"🔧 Generated worker name: {worker_name}")
        logging.info(f"   - Addresses: {self.configured_addrs}")
        logging.info(f"   - Hotkey: {hotkey if self.wallet and self.wallet.hotkey else 'None'}")
        logging.info(f"   - Worker Suffix: {worker_suffix}")
        return worker_name

    def sync_and_refresh(self) -> None:
        """
        Sync metagraph, fetch pools, and update proxy configuration if needed.

        Process:
            1. Sync metagraph to get latest network state
            2. Fetch subnet's pool info
            3. Save pool data to persistent storage
            4. Update proxy configuration if pool info changed
        """
        self.metagraph = self.subtensor.get_metagraph_info(netuid=self.config.netuid)
        self.current_block = self.metagraph.block
        logging.info(f"Syncing at block {self.current_block}")

        target_pools = self.get_target_pool()
        if target_pools:
            self.storage.save_pool_data(self.current_block, target_pools)
            logging.info(f"Saved pool data on block: {self.current_block}")

            if self.proxy_manager and target_pools:
                pool_info = list(target_pools.values())[0]

                success = self.proxy_manager.update_config(pool_info)
                if success:
                    logging.info(
                        f"Proxy configuration verified/updated for {pool_info['domain']}:{pool_info['port']}")

    def get_next_sync_block(self) -> tuple[int, str]:
        """
        Get the next block we should sync at and the reason.

        Returns:
            tuple[int, str]: The next block to sync at and a string explaining the reason

        Process:
            1. Calculate next regular sync interval
            2. Check for upcoming epoch boundaries
        """
        next_sync = self.current_block + (
            self.blocks_per_sync - (self.current_block % self.blocks_per_sync)
        )
        sync_reason = "Regular interval"

        blocks_until_epoch = self.blocks_until_next_epoch()
        if blocks_until_epoch > 0:
            epoch_block = self.current_block + blocks_until_epoch
            if epoch_block < next_sync:
                next_sync = epoch_block
                sync_reason = "Epoch boundary"

        return next_sync, sync_reason

    def set_weights(self):
        """
        Sets the miner weights for self.uid to 65535.
        """
        try:
            # Set the weights on chain via our subtensor connection.
            result, msg = self.subtensor.set_weights(
                wallet=self.wallet,
                netuid=self.config.netuid,
                uids=[self.uid],
                weights=[65535],
                wait_for_finalization=False,
                wait_for_inclusion=False,
                version_key=getattr(self, 'spec_version', 1),
            )
            # sync once, ensure get latest chain state
            logging.info(f'set_weights: my uid: {self.uid}, weights: 65535, last_update: {self.metagraph.last_update[self.uid]}, block: {self.current_block}')
            if result is True:
                logging.info('set_weights on chain successfully!')
            else:
                logging.error('set_weights failed', msg)
        except Exception as e:
            logging.error(f'set_weights failed: {e}')
    def update_axon_on_chain(self):
        """Updates the axon information on the chain to refresh last_update."""
        if not self.axon:
            return

        try:
            # Serve axon to update axon information on chain
            self.subtensor.serve_axon(
                netuid=self.config.netuid,
                axon=self.axon,
            )
            logging.debug(f"Updated axon information on chain for miner uid: {self.uid}, current block: {self.current_block}, last_update: {self.metagraph.last_update[self.uid]}")

        except Exception as e:
            logging.warning(f"Failed to update axon on chain via subtensor.serve_axon(): {e}")
            # Fallback to axon.serve() if subtensor.serve_axon() fails
            try:
                self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)
                logging.debug(f"Fallback to axon.serve() successful for miner uid: {self.uid}")
            except Exception as fallback_error:
                logging.error(f"Both subtensor.serve_axon() and axon.serve() failed: {fallback_error}")

    def run_in_background_thread(self):
        """
        Starts the miner's operations in a separate background thread.
        This is useful for non-blocking operations.
        """
        if not self.is_running:
            logging.debug("Starting miner in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the miner's operations that are running in the background thread.
        """
        if self.is_running:
            logging.debug("Stopping miner in background thread.")
            self.should_exit = True
            if self.thread is not None:
                self.thread.join(5)
            self.is_running = False
            logging.debug("Stopped")

    def __enter__(self):
        """
        Starts the miner's operations in a background thread upon entering the context.
        This method facilitates the use of the miner in a 'with' statement.
        """
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the miner's background operations upon exiting the context.
        This method facilitates the use of the miner in a 'with' statement.
        """
        self.stop_run_thread()

    def run(self) -> None:
        """
        Run the enhanced miner combining proxy mining with axon services.

        Process:
            1. Perform initial sync to get latest chain state
            2. Start axon server if enabled
            3. Calculate the next sync point
            4. Enter main loop:
                - Wait for next sync block
                - Update metagraph and pool data
                - Update mining schedule if needed
                - Set weights periodically
                - Update axon information
                - Calculate next sync point
                - Log mining status and performance
        """
        logging.info("Starting Enhanced DogeLayer Miner main loop")

        # Initial sync
        self.sync_and_refresh()
        logging.info(f"Performed initial sync at block {self.current_block}")

        # Start axon server if enabled
        if self.axon:
            logging.info(f"Serving miner axon {self.axon} on network: {self.config.subtensor.chain_endpoint} with netuid: {self.config.netuid}")

            # Update axon information on chain to refresh last_update
            self.update_axon_on_chain()

            # Start axon server
            self.axon.start()
            logging.info(f"Miner axon started at block: {self.current_block}")

        next_sync_block, sync_reason = self.get_next_sync_block()
        logging.info(f"Next sync at block: {next_sync_block} | Reason: {sync_reason}")

        step = 0
        epoch_length = getattr(self.config.neuron, 'epoch_length', self.tempo)

        while not self.should_exit:
            try:
                # 使用 taoillium 的权重设置逻辑
                if getattr(self.config, 'enable_weight_setting', False):
                    # For miners, since last_update doesn't change, we use a different epoch calculation
                    # We can use the current block number to determine when to sync
                    current_block = self.current_block
                    epoch_start_block = (current_block // epoch_length) * epoch_length
                    logging.trace(f"Current block: {current_block}, epoch_start_block: {epoch_start_block}, epoch_length: {epoch_length}")

                    # Wait until we reach the next epoch block
                    while current_block < epoch_start_block + epoch_length:
                        # Wait before checking again.
                        time.sleep(12)  # 12 seconds per block
                        current_block = self.subtensor.get_current_block()
                        self.current_block = current_block
                        logging.trace(f"Current block: {current_block}")

                        # Check if we should exit.
                        if self.should_exit:
                            break

                    # Sync metagraph and set weights at epoch boundary
                    if not self.should_exit:
                        logging.info(f"🎯 Epoch boundary reached! Setting weights at block {current_block}")
                        self.sync_and_refresh()
                        self.set_weights()
                        self.update_axon_on_chain()
                        step += 1
                else:
                    # 原有的同步逻辑（不设置权重）
                    if self.subtensor.wait_for_block(next_sync_block):
                        # Sync and refresh pool data
                        self.sync_and_refresh()
                        next_sync_block, sync_reason = self.get_next_sync_block()

                        # Update axon information on chain to refresh last_update
                        if self.axon:
                            self.update_axon_on_chain()
                        step += 1

                        # Log status
                        incentive = self.metagraph.incentives[self.uid] if hasattr(self.metagraph, 'incentives') else 0
                        blocks_since_epoch = getattr(self.metagraph, 'blocks_since_last_step', 0)

                        worker_name = getattr(self, '_cached_worker_name', None)
                        if not worker_name:
                            worker_name = self._generate_worker_name()
                            self._cached_worker_name = worker_name
                            
                        logging.info(
                            f"Block: {self.current_block} | "
                            f"Next sync: {next_sync_block} | "
                            f"Reason: {sync_reason} | "
                            f"Incentive: {incentive} | "
                            f"Blocks since epoch: {blocks_since_epoch} | "
                            f"Worker: {worker_name} | "
                            f"Proxy: {'Active' if self.proxy_manager else 'Inactive'} | "
                            f"Axon: {'Active' if self.axon else 'Inactive'}"
                        )
                    else:
                        logging.warning("Timeout waiting for block, retrying...")
                        continue

            except KeyboardInterrupt:
                logging.success("Enhanced Miner killed by keyboard interrupt.")
                self.should_exit = True
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                logging.error(traceback.format_exc())
                continue

        # Cleanup
        if self.axon:
            self.axon.stop()
            logging.info("Axon server stopped")

        logging.info("Enhanced DogeLayer Miner stopped")


if __name__ == "__main__":
    load_dotenv()

    try:
        miner = EnhancedDogeLayerMiner()
        logging.info("Enhanced DogeLayer Miner initialized successfully")

        # Run the miner
        miner.run()

    except KeyboardInterrupt:
        logging.info("Miner stopped by user")
    except Exception as e:
        logging.error(f"Failed to start miner: {e}")
        logging.error(traceback.format_exc())