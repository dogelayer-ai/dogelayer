#!/usr/bin/env python3
"""
简单验证者程序 - 保持子网活跃
"""
import bittensor as bt
import time
import argparse
import logging

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="简单验证者程序")
    parser.add_argument("--wallet.name", type=str, default="bob", dest="wallet_name", help="钱包名称")
    parser.add_argument("--wallet.hotkey", type=str, default="default", dest="wallet_hotkey", help="热键名称")
    parser.add_argument("--subtensor.network", type=str, default="ws://127.0.0.1:9944", dest="subtensor_network", help="网络地址")
    parser.add_argument("--netuid", type=int, default=2, help="子网ID")
    parser.add_argument("--logging.info", action="store_true", dest="logging_info", help="启用详细日志")
    
    args = parser.parse_args()
    
    # 配置日志
    if args.logging_info:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    print(f"🚀 启动简单验证者程序")
    print(f"  钱包: {args.wallet_name}")
    print(f"  热键: {args.wallet_hotkey}")
    print(f"  网络: {args.subtensor_network}")
    print(f"  子网ID: {args.netuid}")
    print("")
    
    try:
        # 初始化subtensor
        subtensor = bt.subtensor(network=args.subtensor_network)
        
        # 初始化钱包
        wallet = bt.wallet(name=args.wallet_name, hotkey=args.wallet_hotkey)
        
        print("✅ 验证者初始化完成")
        
        # 主循环
        epoch_count = 0
        while True:
            try:
                # 同步元图
                metagraph = subtensor.metagraph(netuid=args.netuid)
                
                # 检查是否注册
                if wallet.hotkey.ss58_address not in metagraph.hotkeys:
                    print(f"❌ 热键 {wallet.hotkey.ss58_address} 未在子网 {args.netuid} 中注册")
                    time.sleep(30)
                    continue
                
                # 获取UID
                uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
                
                # 设置权重（简单的均匀分布）
                weights = [1.0 / len(metagraph.hotkeys)] * len(metagraph.hotkeys)
                uids = list(range(len(metagraph.hotkeys)))
                
                # 提交权重
                result = subtensor.set_weights(
                    netuid=args.netuid,
                    wallet=wallet,
                    uids=uids,
                    weights=weights,
                    wait_for_inclusion=True,
                    wait_for_finalization=True
                )
                
                epoch_count += 1
                print(f"✅ Epoch {epoch_count}: 权重设置成功")
                print(f"   UID: {uid}")
                print(f"   权重: {weights[uid]:.4f}")
                print(f"   子网大小: {len(metagraph.hotkeys)}")
                
                # 等待下一个epoch
                time.sleep(12)  # 本地网络epoch时间较短
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(30)
                
    except KeyboardInterrupt:
        print("\n🛑 验证者程序停止")
    except Exception as e:
        print(f"❌ 致命错误: {e}")

if __name__ == "__main__":
    main()