"""
智能响应缓存系统
缓存相同问题的响应，提高响应速度
"""

import time
import json
import hashlib
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from threading import Lock

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    response: Dict
    created_at: float
    last_accessed: float
    access_count: int
    topic_context_hash: str
    
    def to_dict(self):
        return asdict(self)

class ResponseCache:
    """智能响应缓存系统"""
    
    def __init__(self, max_size: int = 1000, max_age_hours: int = 24):
        self.max_size = max_size
        self.max_age_hours = max_age_hours
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        
    def _generate_cache_key(self, message: str, context: Dict) -> str:
        """生成缓存键"""
        # 结合消息内容和上下文摘要生成唯一键
        context_summary = context.get("summary", "")
        key_data = f"{message}|{context_summary}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _generate_context_hash(self, context: Dict) -> str:
        """生成上下文哈希"""
        context_data = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_data.encode()).hexdigest()
    
    def get(self, message: str, context: Dict) -> Optional[Dict]:
        """获取缓存的响应"""
        with self.lock:
            cache_key = self._generate_cache_key(message, context)
            context_hash = self._generate_context_hash(context)
            
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                
                # 检查上下文是否匹配
                if entry.topic_context_hash != context_hash:
                    return None
                
                # 检查缓存是否过期
                if self._is_expired(entry):
                    del self.cache[cache_key]
                    return None
                
                # 更新访问信息
                entry.last_accessed = time.time()
                entry.access_count += 1
                
                return entry.response.copy()
            
            return None
    
    def put(self, message: str, context: Dict, response: Dict) -> bool:
        """存储响应到缓存"""
        with self.lock:
            cache_key = self._generate_cache_key(message, context)
            context_hash = self._generate_context_hash(context)
            
            # 检查缓存大小
            if len(self.cache) >= self.max_size:
                self._cleanup_old_entries()
            
            # 创建缓存条目
            entry = CacheEntry(
                key=cache_key,
                response=response,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                topic_context_hash=context_hash
            )
            
            self.cache[cache_key] = entry
            return True
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否过期"""
        max_age_seconds = self.max_age_hours * 3600
        return (time.time() - entry.created_at) > max_age_seconds
    
    def _cleanup_old_entries(self):
        """清理过期和最少使用的条目"""
        current_time = time.time()
        
        # 按最后访问时间排序
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda x: (x.last_accessed, x.access_count)
        )
        
        # 删除最旧的20%条目
        entries_to_remove = max(1, len(sorted_entries) // 5)
        
        for i in range(entries_to_remove):
            if sorted_entries[i].key in self.cache:
                del self.cache[sorted_entries[i].key]
    
    def remove_by_topic(self, topic_id: str) -> int:
        """删除指定话题的所有缓存"""
        with self.lock:
            entries_to_remove = []
            
            for key, entry in self.cache.items():
                # 检查响应中是否包含该话题ID
                if entry.response.get("topic_id") == topic_id:
                    entries_to_remove.append(key)
            
            for key in entries_to_remove:
                del self.cache[key]
            
            return len(entries_to_remove)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self.lock:
            total_entries = len(self.cache)
            total_access_count = sum(entry.access_count for entry in self.cache.values())
            avg_access_count = total_access_count / total_entries if total_entries > 0 else 0
            
            # 计算平均年龄
            current_time = time.time()
            avg_age = sum(current_time - entry.created_at for entry in self.cache.values()) / total_entries if total_entries > 0 else 0
            
            return {
                "total_entries": total_entries,
                "max_size": self.max_size,
                "total_access_count": total_access_count,
                "average_access_count": avg_access_count,
                "average_age_seconds": avg_age,
                "hit_rate": self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率（简化版本）"""
        # 这里需要更复杂的逻辑来跟踪命中率
        # 简化版本：基于条目访问次数
        if not self.cache:
            return 0.0
        
        total_access = sum(entry.access_count for entry in self.cache.values())
        return min(1.0, total_access / (len(self.cache) * 10))  # 假设平均每个条目应该被访问10次
    
    def get_top_accessed(self, limit: int = 10) -> List[Dict]:
        """获取访问次数最多的缓存条目"""
        with self.lock:
            sorted_entries = sorted(
                self.cache.values(),
                key=lambda x: x.access_count,
                reverse=True
            )
            
            return [entry.to_dict() for entry in sorted_entries[:limit]]
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)