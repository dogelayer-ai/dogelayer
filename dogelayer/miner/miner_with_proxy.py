import argparse
import os
import traceback

from bittensor import logging
from dotenv import load_dotenv

from dogelayer.core.chain_data.pool_info import PoolInfo
from dogelayer.core.pool import PoolIndex
from dogelayer.miner import BaseMiner
from dogelayer.miner.proxy import (
    get_proxy_manager,
    BraiinsProxyManager,
    TaohashProxyManager,
)

DEFAULT_SYNC_FREQUENCY = 6


class TaoHashMiner(BaseMiner):
    """
    TaoHash Multi-Currency Miner implementation.

    This miner supports merged mining for LTC, DOGE, and BTC,
    connecting to the subnet's pool and maintaining
    proxy configuration in sync with the subnets's published pool info.
    """

    def __init__(self):
        """
        Initialize the TaoHash miner with configuration and setup.

        Process:
            1. Perform base miner initialization
            2. Set up multi-currency address validation
            3. Set up proxy manager if enabled
        """
        # Base miner initialization
        super().__init__()

        # Validate addresses (at least one must be provided)
        self.configured_addrs = self._validate_addresses()

        self.proxy_manager = None
        if self.config.use_proxy:
            self.proxy_manager = get_proxy_manager(
                proxy_type=self.config.proxy_type, config=self.config
            )

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

    def add_args(self, parser: argparse.ArgumentParser):
        """Add TaoHash-specific arguments to the parser."""
        super().add_args(parser)

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
            choices=["taohash", "braiins"],
            default=os.getenv("PROXY_TYPE", "taohash"),
            help="Proxy type to use (taohash or braiins)",
        )

        args, _ = parser.parse_known_args()
        if hasattr(args, "proxy_type"):
            if args.proxy_type == "taohash":
                TaohashProxyManager.add_args(parser)
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
            logging.error("Subnet's pool has not published information")
            return {}

        if subnet_pool_info.pool_index != PoolIndex.Proxy:
            logging.error(
                f"Subnet's pool is not a Proxy pool (index: {subnet_pool_info.pool_index}). "
                f"Expected PoolIndex.Proxy ({PoolIndex.Proxy})"
            )
            return {}

        subnet_pool_info.extra_data["full_username"] = self._generate_worker_name(
        )

        return {self.pool_hotkey: subnet_pool_info.to_json()}

    def _generate_worker_name(self):
        """Generate worker name from configured addresses."""
        # Use the addresses validated during initialization
        worker_name = f"{'-'.join(self.configured_addrs)}.{self.worker_id}"
        logging.info(f"Generated worker name: {worker_name}")
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
        self.metagraph = self.subtensor.get_metagraph_info(
            netuid=self.config.netuid)
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

    def run(self) -> None:
        """
        Run the main mining loop.

        Process:
            1. Perform initial sync to get latest chain state
            2. Calculate the next sync point
            3. Enter main loop:
                - Wait for next sync block
                - Update metagraph and pool data
                - Update mining schedule if needed
                - Calculate next sync point
                - Log mining status and performance
        """
        logging.info("Starting main loop")

        self.sync_and_refresh()
        logging.info(f"Performed initial sync at block {self.current_block}")

        next_sync_block, sync_reason = self.get_next_sync_block()
        logging.info(
            f"Next sync at block: {next_sync_block} | Reason: {sync_reason}")

        while True:
            try:
                if self.subtensor.wait_for_block(next_sync_block):
                    self.sync_and_refresh()
                    next_sync_block, sync_reason = self.get_next_sync_block()

                    logging.info(
                        f"Block: {self.current_block} | "
                        f"Next sync: {next_sync_block} | "
                        f"Reason: {sync_reason} | "
                        f"Incentive: {self.metagraph.incentives[self.uid]} | "
                        f"Blocks since epoch: {self.metagraph.blocks_since_last_step}"
                    )
                else:
                    logging.warning("Timeout waiting for block, retrying...")
                    continue

            except KeyboardInterrupt:
                logging.success("Miner killed by keyboard interrupt.")
                break
            except Exception:
                logging.error(traceback.format_exc())
                continue


if __name__ == "__main__":
    load_dotenv()
    miner = TaoHashMiner()
    miner.run()
