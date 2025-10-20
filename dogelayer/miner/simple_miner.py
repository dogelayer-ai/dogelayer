#!/usr/bin/env python3
"""
SimpleMiner - A simplified TaoHash miner for testing subnet connections.

This script connects to a TaoHash subnet and displays basic mining information
without performing actual mining operations. It's useful for:
- Testing subnet connectivity
- Verifying wallet registration
- Learning the mining setup process

Usage:
    python simple_miner.py --wallet.name YOUR_WALLET --wallet.hotkey YOUR_HOTKEY --subtensor.network finney

    # For custom test network
    python simple_miner.py --wallet.name YOUR_WALLET --wallet.hotkey YOUR_HOTKEY --subtensor.network test --subtensor.chain_endpoint ws://175.41.141.7:9944 --netuid 331
"""

import argparse
import os
import sys
import time
import traceback

from bittensor import logging, Subtensor, config
from bittensor_wallet.bittensor_wallet import Wallet

from dogelayer.core.chain_data.pool_info import get_pool_info
from dogelayer.core.pool import PoolIndex


class SimpleMiner:
    """
    简化的TaoHash挖矿程序，用于测试子网连接

    这个类不依赖BaseMiner，而是直接使用Bittensor SDK来：
    1. 连接到配置的子网
    2. 验证钱包注册状态
    3. 显示基本的挖矿信息
    4. 监控子网状态变化
    """

    def __init__(self, config):
        """
        初始化SimpleMiner

        Args:
            config: Bittensor配置对象
        """
        self.config = config

        logging.info("初始化SimpleMiner...")

        # 初始化Bittensor组件
        self.wallet = Wallet(config=config)
        self.subtensor = Subtensor(config=config)

        logging.info(f"连接网络: {self.subtensor.network}")
        logging.info(
            f"Chain endpoint: {getattr(self.subtensor, 'chain_endpoint', 'Default')}")
        logging.info(f"目标子网UID: {self.config.netuid}")
        logging.info(f"钱包: {self.wallet}")

        # 验证钱包注册
        self._verify_registration()

        # 获取子网信息
        self.metagraph = self.subtensor.get_metagraph_info(
            netuid=self.config.netuid)
        self.uid = self.metagraph.hotkeys.index(
            self.wallet.hotkey.ss58_address)
        self.tempo = self.subtensor.tempo(self.config.netuid)
        self.step = 0

        logging.success(f"✓ SimpleMiner初始化完成 - UID: {self.uid}")

    def _verify_registration(self):
        """验证钱包是否在子网中注册"""
        logging.info("检查钱包注册状态...")

        try:
            metagraph = self.subtensor.get_metagraph_info(
                netuid=self.config.netuid)

            if self.wallet.hotkey.ss58_address not in metagraph.hotkeys:
                logging.error(
                    f"\n❌ 钱包 {self.wallet} 未在子网 {self.config.netuid} 中注册\n"
                    f"   请运行 'btcli subnet register' 进行注册"
                )
                sys.exit(1)

            logging.success(f"✓ 钱包已在子网 {self.config.netuid} 中注册")

        except Exception as e:
            logging.error(f"验证注册状态失败: {e}")
            sys.exit(1)

    def get_subnet_info(self):
        """获取子网池信息"""
        try:
            logging.info("获取子网池信息...")

            # 获取子网owner
            owner_hotkey = self.subtensor.query_subtensor(
                "SubnetOwnerHotkey",
                params=[self.config.netuid]
            )

            if not owner_hotkey:
                logging.warning("无法获取子网owner信息")
                return None

            # 获取池信息
            pool_info = get_pool_info(
                self.subtensor, self.config.netuid, owner_hotkey)

            if not pool_info:
                logging.warning("未找到子网池信息")
                return None

            if pool_info.pool_index != PoolIndex.Proxy:
                logging.warning(f"池类型不是Proxy (发现: {pool_info.pool_index})")

            return pool_info

        except Exception as e:
            logging.error(f"获取子网信息错误: {e}")
            return None

    def display_status(self):
        """显示当前状态信息"""
        try:
            # 更新metagraph
            self.metagraph = self.subtensor.get_metagraph_info(
                netuid=self.config.netuid)
            current_block = self.metagraph.block

            # 获取当前状态
            incentive = self.metagraph.incentives[self.uid] if self.uid < len(
                self.metagraph.incentives) else 0
            emission = self.metagraph.emission[self.uid] if self.uid < len(
                self.metagraph.emission) else 0
            stake = self.metagraph.stake[self.uid] if self.uid < len(
                self.metagraph.stake) else 0

            # 获取池信息
            pool_info = self.get_subnet_info()

            print("\n" + "=" * 60)
            print("SIMPLE MINER 状态")
            print("=" * 60)

            print(f"\n网络信息:")
            print(f"  网络: {self.subtensor.network}")
            print(
                f"  Chain endpoint: {getattr(self.subtensor, 'chain_endpoint', 'Default')}")
            print(f"  子网UID: {self.config.netuid}")
            print(f"  当前区块: {current_block}")
            print(f"  Tempo: {self.tempo} blocks")

            print(f"\n钱包信息:")
            print(f"  钱包名称: {self.wallet.name}")
            print(f"  Hotkey: {self.wallet.hotkey.ss58_address}")
            print(f"  在子网中的UID: {self.uid}")

            print(f"\n当前状态:")
            print(f"  Incentive: {incentive:.6f}")
            print(f"  Emission: {emission:.6f}")
            print(f"  Stake: {stake:.3f}")
            print(f"  Step: {self.step}")

            if pool_info:
                print(f"\n子网池信息:")
                print(f"  池域名/IP: {pool_info.domain or pool_info.ip}")
                print(f"  池端口: {pool_info.port}")
                if pool_info.high_diff_port:
                    print(f"  高难度端口: {pool_info.high_diff_port}")
                print(f"  密码: {pool_info.password or 'x'}")
                print(f"  池类型: {pool_info.pool_index}")
            else:
                print(f"\n子网池信息: 未找到")

            print("=" * 60)

        except Exception as e:
            logging.error(f"显示状态错误: {e}")

    def run(self):
        """运行SimpleMiner主循环"""
        logging.info("启动SimpleMiner监控循环...")
        logging.info(f"每 {self.tempo} 个区块更新一次状态")

        # 显示初始状态
        self.display_status()

        # 计算下次更新区块
        current_block = self.metagraph.block
        next_update_block = current_block + self.tempo

        logging.info(f"下次状态更新区块: {next_update_block}")

        while True:
            try:
                # 等待下一个更新区块
                if self.subtensor.wait_for_block(next_update_block):
                    self.step += 1

                    # 显示更新后的状态
                    self.display_status()

                    # 计算下次更新区块
                    current_block = self.metagraph.block
                    next_update_block = current_block + self.tempo

                    logging.info(f"下次状态更新区块: {next_update_block}")

                else:
                    logging.warning("等待区块超时，重试中...")
                    continue

            except KeyboardInterrupt:
                logging.success("SimpleMiner被用户中断停止")
                break
            except Exception as e:
                logging.error(f"SimpleMiner运行错误: {e}")
                logging.error(traceback.format_exc())
                time.sleep(30)  # 出错后等待30秒继续


def main():
    """
    主函数 - 启动SimpleMiner
    """
    try:
        # 创建参数解析器，使用与miner.py相同的模式
        parser = argparse.ArgumentParser(
            description="SimpleMiner - 简化的TaoHash子网连接测试工具"
        )

        # 添加子网参数
        parser.add_argument(
            "--netuid",
            type=int,
            default=os.getenv("NETUID", 14),
            help="子网UID (默认: 14)",
        )

        # 添加Bittensor标准参数
        Wallet.add_args(parser)
        Subtensor.add_args(parser)
        logging.add_args(parser)

        # 解析配置
        config_obj = config(parser)

        # 初始化日志
        logging(config=config_obj, logging_dir=config_obj.full_path)

        logging.info("启动SimpleMiner...")
        logging.info(
            f"配置的网络: {getattr(config_obj.subtensor, 'network', 'finney')}")
        logging.info(
            f"配置的chain endpoint: {getattr(config_obj.subtensor, 'chain_endpoint', 'Default')}")
        logging.info(f"配置的子网UID: {config_obj.netuid}")

        # 创建并运行SimpleMiner
        miner = SimpleMiner(config_obj)
        miner.run()

    except KeyboardInterrupt:
        logging.info("收到停止信号，正在关闭SimpleMiner...")
    except Exception as e:
        logging.error(f"SimpleMiner启动失败: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
