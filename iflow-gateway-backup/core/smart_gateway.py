"""
智能网关 - 整合所有组件
实现完整的网关数据流处理功能
"""

import time
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .context_manager import ContextManager
from .response_cache import ResponseCache
from .topic_summarizer import TopicSummarizer, SummaryConfig

@dataclass
class GatewayConfig:
    """网关配置"""
    max_topics: int = 5
    max_tokens_per_topic: int = 2000
    max_cache_size: int = 1000
    max_summary_length: int = 500
    chunk_size: int = 100
    timeout_seconds: int = 60
    enable_compression: bool = True
    enable_incremental_summary: bool = True

class SmartGateway:
    """智能网关 - 整合所有组件"""
    
    def __init__(self, config: GatewayConfig = None):
        self.config = config or GatewayConfig()
        
        # 初始化组件
        self.context_manager = ContextManager(
            max_topics=self.config.max_topics,
            max_tokens_per_topic=self.config.max_tokens_per_topic
        )
        
        self.response_cache = ResponseCache(
            max_size=self.config.max_cache_size
        )
        
        self.topic_summarizer = TopicSummarizer(
            SummaryConfig(
                max_summary_length=self.config.max_summary_length
            )
        )
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "summaries_generated": 0,
            "contexts_truncated": 0,
            "errors": 0
        }
    
    async def process_request(self, message: str, topic_id: str = None, user_id: str = None) -> Dict:
        """处理请求"""
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # 生成或获取话题ID
            if topic_id is None:
                topic_id = self._generate_topic_id(user_id or "default")
            
            # 获取上下文
            context = self.context_manager.get_context(topic_id)
            
            # 检查缓存
            cached_response = self.response_cache.get(message, context)
            if cached_response:
                self.stats["cache_hits"] += 1
                cached_response["from_cache"] = True
                cached_response["processing_time"] = time.time() - start_time
                return cached_response
            
            self.stats["cache_misses"] += 1
            
            # 添加消息到上下文
            self.context_manager.add_message(topic_id, "user", message)
            updated_context = self.context_manager.get_context(topic_id)
            
            # 生成响应（这里应该是调用实际的AI模型）
            response_content = await self._generate_ai_response(message, updated_context)
            
            # 处理响应
            processed_response = self._process_ai_response(
                response_content, topic_id, updated_context
            )
            
            # 缓存响应
            self.response_cache.put(message, context, processed_response)
            
            # 添加AI回复到上下文
            self.context_manager.add_message(topic_id, "assistant", response_content)
            
            # 更新统计
            processed_response["processing_time"] = time.time() - start_time
            processed_response["from_cache"] = False
            
            return processed_response
            
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "error": str(e),
                "error_type": "processing_error",
                "topic_id": topic_id,
                "processing_time": time.time() - start_time
            }
    
    def switch_topic(self, new_topic_id: str, initial_message: str = "", user_id: str = None) -> Dict:
        """切换话题"""
        try:
            if user_id:
                new_topic_id = f"{user_id}_{new_topic_id}"
            
            success = self.context_manager.switch_topic(new_topic_id, initial_message)
            
            # 清理相关缓存
            if success:
                self.response_cache.remove_by_topic(new_topic_id)
            
            return {
                "success": success,
                "topic_id": new_topic_id,
                "message": "话题切换成功" if success else "话题切换失败"
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "topic_id": new_topic_id
            }
    
    def get_topic_summary(self, topic_id: str) -> Dict:
        """获取话题摘要"""
        try:
            summary = self.context_manager.get_topic_summary(topic_id)
            return {
                "topic_id": topic_id,
                "summary": summary,
                "has_summary": bool(summary)
            }
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "topic_id": topic_id,
                "error": str(e),
                "has_summary": False
            }
    
    def get_context_info(self, topic_id: str) -> Dict:
        """获取上下文信息"""
        try:
            context = self.context_manager.get_context(topic_id)
            stats = self.context_manager.get_stats()
            
            return {
                "topic_id": topic_id,
                "context": context,
                "stats": stats,
                "cache_stats": self.response_cache.get_stats()
            }
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "topic_id": topic_id,
                "error": str(e)
            }
    
    def get_all_topics(self) -> Dict:
        """获取所有话题信息"""
        try:
            topics = self.context_manager.get_all_topics()
            stats = self.context_manager.get_stats()
            cache_stats = self.response_cache.get_stats()
            
            return {
                "topics": topics,
                "stats": stats,
                "cache_stats": cache_stats,
                "total_stats": self.stats
            }
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "error": str(e),
                "total_stats": self.stats
            }
    
    def cleanup(self) -> Dict:
        """清理过期数据"""
        try:
            # 清理过期话题
            old_topics_removed = self.context_manager.cleanup_old_topics()
            
            # 清理过期缓存
            expired_cache_removed = self.response_cache.cleanup_expired()
            
            return {
                "old_topics_removed": old_topics_removed,
                "expired_cache_removed": expired_cache_removed,
                "success": True
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    # 私有方法
    def _generate_topic_id(self, user_id: str) -> str:
        """生成话题ID"""
        import hashlib
        timestamp = str(int(time.time()))
        unique_id = f"{user_id}_{timestamp}"
        return hashlib.md5(unique_id.encode()).hexdigest()[:16]
    
    async def _generate_ai_response(self, message: str, context: Dict) -> str:
        """生成AI响应（模拟实现）"""
        # 这里应该是调用实际的AI模型
        # 现在返回模拟响应
        
        # 模拟AI处理延迟
        await asyncio.sleep(0.1)
        
        # 基于上下文生成响应
        if context.get("summary"):
            summary = context["summary"]
            return f"我理解了之前的对话内容：{summary}。针对您的问题：{message}，我会为您提供帮助。"
        else:
            return f"收到您的问题：{message}。我会为您提供详细的解答和建议。"
    
    def _process_ai_response(self, response_content: str, topic_id: str, context: Dict) -> Dict:
        """处理AI响应"""
        processed_response = {
            "topic_id": topic_id,
            "response": response_content,
            "timestamp": time.time(),
            "context_info": {
                "token_count": context.get("token_count", 0),
                "messages_count": len(context.get("messages", [])),
                "has_summary": bool(context.get("summary", ""))
            }
        }
        
        # 如果需要分段处理
        if len(response_content) > self.config.chunk_size:
            chunks = self._chunk_response(response_content)
            processed_response["chunks"] = chunks
            processed_response["chunked"] = True
        else:
            processed_response["chunks"] = [response_content]
            processed_response["chunked"] = False
        
        return processed_response
    
    def _chunk_response(self, response: str) -> List[str]:
        """将响应分块"""
        chunks = []
        
        # 按句子分割
        sentences = re.split(r'[。！？]', response)
        current_chunk = ""
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            if len(current_chunk) + len(sentence) <= self.config.chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        cache_stats = self.response_cache.get_stats()
        context_stats = self.context_manager.get_stats()
        
        # 计算命中率
        hit_rate = (self.stats["cache_hits"] / 
                   max(1, self.stats["cache_hits"] + self.stats["cache_misses"]))
        
        # 计算平均处理时间（简化版本）
        avg_processing_time = 0.5  # 假设平均0.5秒
        
        return {
            "cache_hit_rate": hit_rate,
            "cache_stats": cache_stats,
            "context_stats": context_stats,
            "total_requests": self.stats["total_requests"],
            "total_errors": self.stats["errors"],
            "avg_processing_time": avg_processing_time,
            "summaries_generated": self.stats["summaries_generated"],
            "contexts_truncated": self.stats["contexts_truncated"]
        }