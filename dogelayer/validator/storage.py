from typing import Optional, Union
import asyncio
import aiohttp
import json
import os
import concurrent.futures
from datetime import datetime

from bittensor.core.config import Config
from bittensor.utils.btlogging import logging

from dogelayer.core.storage import BaseJsonStorage, BaseRedisStorage


class JsonValidatorStorage(BaseJsonStorage):
    def __init__(self, config: Optional["Config"] = None):
        super().__init__(config)
        self.validator_id = self.generate_user_id(config)
        # 统一数据库API配置 - 直接使用环境变量
        self.proxy_api_url = os.getenv('SUBNET_PROXY_API_URL', 'http://127.0.0.1:8888')
        self.proxy_api_token = os.getenv('SUBNET_PROXY_API_TOKEN', '')
        
        # 处理submit_validator_info配置，默认true
        self.submit_to_db = os.getenv('SUBMIT_VALIDATOR_INFO', 'true').lower() == 'true'
        
        # 创建线程池执行器用于异步任务
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_submit")

    def save_state(self, state: dict) -> None:
        """Save the validator state to a single JSON file."""
        prefix = f"{self.validator_id}_state"
        self.save_data(key="current", data=state, prefix=prefix)
        logging.debug(f"Saved validator state at block {state['current_block']}")
        
        # 额外提交到统一数据库
        if self.submit_to_db:
            logging.info(f"🔄 准备提交验证者信息到数据库: {self.proxy_api_url}")
            # 使用线程池执行器运行异步任务
            def run_async_tasks():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 并行提交验证者信息和矿工评分
                    miner_scores = self._extract_miner_scores(state)
                    logging.info(f"🔄 准备提交矿工评分数据: {len(miner_scores)} 条记录")
                    
                    # 使用asyncio.gather并行执行
                    loop.run_until_complete(asyncio.gather(
                        self._submit_validator_info(state),
                        self._submit_miner_scores(miner_scores),
                        return_exceptions=True
                    ))
                    
                except Exception as e:
                    logging.error(f"异步提交任务失败: {e}")
                finally:
                    loop.close()
            
            # 使用线程池提交任务
            self.executor.submit(run_async_tasks)
        else:
            logging.warning("⚠️ submit_to_db 配置为 False，跳过数据库提交")

    def load_latest_state(self) -> dict:
        """Load the latest saved validator state."""
        prefix = f"{self.validator_id}_state"
        return self.load_data(key="current", prefix=prefix)
    
    def close(self):
        """关闭线程池执行器，释放资源"""
        if hasattr(self, 'executor') and self.executor:
            self.executor.shutdown(wait=True)
            logging.debug("线程池执行器已关闭")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=False)  # 不等待，避免阻塞垃圾回收
        except Exception:
            # 在析构函数中忽略异常，避免影响垃圾回收
            pass
    
    async def _submit_validator_info(self, state: dict) -> None:
        """提交验证者信息到统一数据库"""
        try:
            # 从state中提取验证者信息
            validator_info = self._extract_validator_info(state)
            
            # 发送到proxy API
            headers = {}
            if self.proxy_api_token:
                headers['Authorization'] = f'Bearer {self.proxy_api_token}'
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.proxy_api_url}/api/validators/submit_info",
                    json=validator_info,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ 验证者信息提交成功: {validator_info['hotkey'][:8]}...")
                    else:
                        logging.warning(f"验证者信息提交失败: {response.status}")
                        
        except Exception as e:
            logging.error(f"提交验证者信息失败: {e}")
    
    def _extract_validator_info(self, state: dict) -> dict:
        """从验证者状态中提取需要的信息"""
        return {
            "hotkey": state.get("hotkey", ""),
            "coldkey": state.get("coldkey", ""),
            "uid": state.get("uid", 0),
            "netuid": state.get("netuid", 2),
            "current_block": state.get("current_block", 0),
            "validator_stake": state.get("validator_stake", 0.0),
            "last_update": state.get("last_update", 0),
            "scores": state.get("scores", []),
            "weights": state.get("weights", []),
            "timestamp": datetime.now().isoformat(),
            "validator_version": state.get("version", "unknown")
        }
    
    def _extract_miner_scores(self, state: dict) -> list:
        """从验证者状态中提取矿工评分信息"""
        miner_scores = []
        
        # 获取基础信息
        validator_hotkey = state.get("hotkey", "")
        current_block = state.get("current_block", 0)
        scores = state.get("scores", [])
        hotkeys = state.get("hotkeys", [])
        block_at_registration = state.get("block_at_registration", [])
        
        # 直接从state的基础数据构建矿工评分
        for i, hotkey in enumerate(hotkeys):
            if i < len(scores):
                miner_score = {
                    "validator_hotkey": validator_hotkey,
                    "miner_hotkey": hotkey,
                    "miner_uid": i,
                    "netuid": state.get("netuid", 2),
                    "evaluation_block": current_block,
                    "score": float(scores[i]) if scores[i] is not None else 0.0,
                    "registration_block": block_at_registration[i] if i < len(block_at_registration) else 0,
                    "evaluation_time": datetime.now().isoformat()
                }
                miner_scores.append(miner_score)
        
        return miner_scores
    
    async def _submit_miner_scores(self, miner_scores: list) -> None:
        """提交矿工评分信息到统一数据库"""
        # 移除空数据检查，确保始终提交（即使是空列表）
        try:
            headers = {}
            if self.proxy_api_token:
                headers['Authorization'] = f'Bearer {self.proxy_api_token}'
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.proxy_api_url}/api/validators/submit_miner_scores",
                    json={"miner_scores": miner_scores},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ 矿工评分提交成功: {len(miner_scores)} 条记录")
                    else:
                        logging.warning(f"矿工评分提交失败: {response.status}")
        except Exception as e:
            logging.error(f"提交矿工评分失败: {e}")


class RedisValidatorStorage(BaseRedisStorage):
    def __init__(self, config: Optional["Config"] = None):
        super().__init__(config)
        self.validator_id = self.generate_user_id(config)
        # 统一数据库API配置 - 直接使用环境变量
        self.proxy_api_url = os.getenv('SUBNET_PROXY_API_URL', 'http://127.0.0.1:8888')
        self.proxy_api_token = os.getenv('SUBNET_PROXY_API_TOKEN', '')
        
        # 处理submit_validator_info配置，默认true
        self.submit_to_db = os.getenv('SUBMIT_VALIDATOR_INFO', 'true').lower() == 'true'
        
        # 创建线程池执行器用于异步任务
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="db_submit")

    def save_state(self, state: dict) -> None:
        """Save the validator state to Redis."""
        prefix = f"{self.validator_id}_state"
        self.save_data(key="current", data=state, prefix=prefix)
        
        # 额外提交到统一数据库
        if self.submit_to_db:
            logging.info(f"🔄 准备提交验证者信息到数据库: {self.proxy_api_url}")
            # 使用线程池执行器运行异步任务
            def run_async_tasks():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 并行提交验证者信息和矿工评分
                    miner_scores = self._extract_miner_scores(state)
                    logging.info(f"🔄 准备提交矿工评分数据: {len(miner_scores)} 条记录")
                    
                    # 使用asyncio.gather并行执行
                    loop.run_until_complete(asyncio.gather(
                        self._submit_validator_info(state),
                        self._submit_miner_scores(miner_scores),
                        return_exceptions=True
                    ))
                    
                except Exception as e:
                    logging.error(f"异步提交任务失败: {e}")
                finally:
                    loop.close()
            
            # 使用线程池提交任务
            self.executor.submit(run_async_tasks)
        else:
            logging.warning("⚠️ submit_to_db 配置为 False，跳过数据库提交")

    def load_latest_state(self) -> dict:
        """Get validator state for specific block."""
        prefix = f"{self.validator_id}_state"
        return self.load_data(key="current", prefix=prefix)
    
    async def _submit_validator_info(self, state: dict) -> None:
        """提交验证者信息到统一数据库"""
        try:
            # 从state中提取验证者信息
            validator_info = self._extract_validator_info(state)
            
            # 发送到proxy API
            headers = {}
            if self.proxy_api_token:
                headers['Authorization'] = f'Bearer {self.proxy_api_token}'
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.proxy_api_url}/api/validators/submit_info",
                    json=validator_info,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ 验证者信息提交成功: {validator_info['hotkey'][:8]}...")
                    else:
                        logging.warning(f"验证者信息提交失败: {response.status}")
                        
        except Exception as e:
            logging.error(f"提交验证者信息失败: {e}")
    
    def _extract_validator_info(self, state: dict) -> dict:
        """从验证者状态中提取需要的信息"""
        return {
            "hotkey": state.get("hotkey", ""),
            "coldkey": state.get("coldkey", ""),
            "uid": state.get("uid", 0),
            "netuid": state.get("netuid", 2),
            "current_block": state.get("current_block", 0),
            "validator_stake": state.get("validator_stake", 0.0),
            "last_update": state.get("last_update", 0),
            "scores": state.get("scores", []),
            "weights": state.get("weights", []),
            "timestamp": datetime.now().isoformat(),
            "validator_version": state.get("version", "unknown")
        }
    
    def _extract_miner_scores(self, state: dict) -> list:
        """从验证者状态中提取矿工评分信息"""
        miner_scores = []
        
        # 获取基础信息
        validator_hotkey = state.get("hotkey", "")
        current_block = state.get("current_block", 0)
        scores = state.get("scores", [])
        hotkeys = state.get("hotkeys", [])
        block_at_registration = state.get("block_at_registration", [])
        
        # 直接从state的基础数据构建矿工评分
        for i, hotkey in enumerate(hotkeys):
            if i < len(scores):
                miner_score = {
                    "validator_hotkey": validator_hotkey,
                    "miner_hotkey": hotkey,
                    "miner_uid": i,
                    "netuid": state.get("netuid", 2),
                    "evaluation_block": current_block,
                    "score": float(scores[i]) if scores[i] is not None else 0.0,
                    "registration_block": block_at_registration[i] if i < len(block_at_registration) else 0,
                    "evaluation_time": datetime.now().isoformat()
                }
                miner_scores.append(miner_score)
        
        return miner_scores
    
    async def _submit_miner_scores(self, miner_scores: list) -> None:
        """提交矿工评分信息到统一数据库"""
        # 移除空数据检查，确保始终提交（即使是空列表）
        try:
            headers = {}
            if self.proxy_api_token:
                headers['Authorization'] = f'Bearer {self.proxy_api_token}'
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.proxy_api_url}/api/validators/submit_miner_scores",
                    json={"miner_scores": miner_scores},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ 矿工评分提交成功: {len(miner_scores)} 条记录")
                    else:
                        logging.warning(f"矿工评分提交失败: {response.status}")
        except Exception as e:
            logging.error(f"提交矿工评分失败: {e}")


STORAGE_CLASSES = {"json": JsonValidatorStorage, "redis": RedisValidatorStorage}


# Factory function to get storage
def get_validator_storage(
    storage_type: str, config: "Config"
) -> Union["JsonValidatorStorage", "RedisValidatorStorage"]:
    """Get a Validator storage instance based on a passed storage type.

    Arguments:
        storage_type: The type of storage to initialize.
        config: The configuration object.

    Returns:
        Storage instance created based on the specified storage type.
    """
    if storage_type not in STORAGE_CLASSES:
        raise ValueError(f"Unknown storage type: {storage_type}")

    storage_class = STORAGE_CLASSES[storage_type]

    try:
        return storage_class(config)
    except Exception as e:
        message = f"Failed to initialize {storage_type} storage: {e}"
        logging.error(message)
        raise Exception(message)
