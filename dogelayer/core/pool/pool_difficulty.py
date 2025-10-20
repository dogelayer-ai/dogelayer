"""
矿池难度获取模块
用于从mining-pool API获取真实的矿池难度，替代网络难度
"""

import os
import logging
import requests
from typing import Optional


class PoolDifficultyAPI:
    """矿池难度API客户端"""
    
    def __init__(self, api_url: Optional[str] = None):
        """
        初始化矿池难度API客户端
        
        Args:
            api_url: 矿池API URL，默认从环境变量MINING_POOL_API_URL获取
        """
        self.api_url = api_url or os.getenv("MINING_POOL_API_URL", "http://localhost:8001")
        self.timeout = 10
        
    def get_pool_difficulty(self) -> Optional[float]:
        """
        获取矿池难度
        
        Returns:
            float: 矿池难度值，失败时返回None
        """
        try:
            url = f"{self.api_url}/api/pool/difficulty"
            
            logging.info(f"Fetching pool difficulty from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            pool_difficulty = data.get("pool_difficulty")
            
            if pool_difficulty is not None:
                logging.info(f"Successfully fetched pool difficulty: {pool_difficulty}")
                return float(pool_difficulty)
            else:
                logging.error(f"Pool difficulty not found in response: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch pool difficulty from {url}: {e}")
            return None
        except (ValueError, KeyError) as e:
            logging.error(f"Failed to parse pool difficulty response: {e}")
            return None
    
    def get_pool_difficulty_with_fallback(self, fallback_difficulty: float = 0.0001) -> float:
        """
        获取矿池难度，失败时使用默认值
        
        Args:
            fallback_difficulty: 默认难度值（基于历史数据的合理估计）
            
        Returns:
            float: 矿池难度值
        """
        difficulty = self.get_pool_difficulty()
        
        if difficulty is not None:
            return difficulty
        else:
            logging.warning(f"Using fallback pool difficulty: {fallback_difficulty}")
            return fallback_difficulty


# 全局实例
_pool_difficulty_api = None


def get_pool_difficulty_api() -> PoolDifficultyAPI:
    """获取全局矿池难度API实例"""
    global _pool_difficulty_api
    if _pool_difficulty_api is None:
        _pool_difficulty_api = PoolDifficultyAPI()
    return _pool_difficulty_api


def get_pool_difficulty() -> Optional[float]:
    """
    便捷函数：获取矿池难度
    
    Returns:
        float: 矿池难度值，失败时返回None
    """
    api = get_pool_difficulty_api()
    return api.get_pool_difficulty()


def get_pool_difficulty_with_fallback(fallback_difficulty: float = 0.0001) -> float:
    """
    便捷函数：获取矿池难度，失败时使用默认值
    
    Args:
        fallback_difficulty: 默认难度值
        
    Returns:
        float: 矿池难度值
    """
    api = get_pool_difficulty_api()
    return api.get_pool_difficulty_with_fallback(fallback_difficulty)
