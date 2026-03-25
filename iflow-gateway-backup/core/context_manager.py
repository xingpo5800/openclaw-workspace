"""
智能上下文管理器
管理对话上下文，实现滑动窗口和话题摘要功能
"""

import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import deque
import hashlib

@dataclass
class Message:
    role: str
    content: str
    timestamp: float
    message_id: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Topic:
    topic_id: str
    messages: List[Message]
    summary: str
    created_at: float
    last_updated: float
    token_count: int
    
    def to_dict(self):
        return asdict(self)

class ContextManager:
    """智能上下文管理器"""
    
    def __init__(self, max_topics: int = 5, max_tokens_per_topic: int = 2000):
        self.max_topics = max_topics
        self.max_tokens_per_topic = max_tokens_per_topic
        self.topics: Dict[str, Topic] = {}
        self.current_topic_id: Optional[str] = None
        
    def create_topic(self, topic_id: str, initial_message: str = "") -> Topic:
        """创建新话题"""
        if len(self.topics) >= self.max_topics:
            # 删除最旧的话题
            oldest_topic = self._get_oldest_topic()
            if oldest_topic:
                del self.topics[oldest_topic.topic_id]
        
        topic = Topic(
            topic_id=topic_id,
            messages=[],
            summary="",
            created_at=time.time(),
            last_updated=time.time(),
            token_count=0
        )
        
        if initial_message:
            self.add_message(topic_id, "user", initial_message)
            
        self.topics[topic_id] = topic
        self.current_topic_id = topic_id
        return topic
    
    def add_message(self, topic_id: str, role: str, content: str) -> bool:
        """添加消息到话题"""
        if topic_id not in self.topics:
            return False
            
        topic = self.topics[topic_id]
        
        # 生成消息ID
        message_id = hashlib.md5(f"{role}{content}{time.time()}".encode()).hexdigest()[:16]
        
        # 创建消息对象
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            message_id=message_id
        )
        
        # 添加消息
        topic.messages.append(message)
        topic.last_updated = time.time()
        
        # 更新token计数（简化计算：1 token ≈ 1.3 characters）
        topic.token_count += len(content) * 1.3
        
        # 检查是否需要生成摘要
        if self._should_summarize(topic):
            self._generate_topic_summary(topic_id)
            
        return True
    
    def get_context(self, topic_id: str, max_tokens: int = None) -> Dict:
        """获取话题上下文"""
        if topic_id not in self.topics:
            return {"messages": [], "summary": "", "token_count": 0}
            
        topic = self.topics[topic_id]
        max_tokens = max_tokens or self.max_tokens_per_topic
        
        # 如果token数量超过限制，进行截断
        if topic.token_count > max_tokens:
            return self._truncate_context(topic, max_tokens)
            
        return {
            "messages": [msg.to_dict() for msg in topic.messages],
            "summary": topic.summary,
            "token_count": topic.token_count,
            "topic_id": topic_id
        }
    
    def switch_topic(self, new_topic_id: str, initial_message: str = "") -> bool:
        """切换到新话题"""
        # 清理当前话题的旧数据（可选）
        if self.current_topic_id and self.current_topic_id != new_topic_id:
            self._cleanup_old_topic(self.current_topic_id)
            
        # 创建或切换到新话题
        if new_topic_id not in self.topics:
            self.create_topic(new_topic_id, initial_message)
        else:
            self.current_topic_id = new_topic_id
            
        return True
    
    def get_topic_summary(self, topic_id: str) -> str:
        """获取话题摘要"""
        if topic_id in self.topics:
            return self.topics[topic_id].summary
        return ""
    
    def update_topic_summary(self, topic_id: str, summary: str) -> bool:
        """更新话题摘要"""
        if topic_id in self.topics:
            self.topics[topic_id].summary = summary
            self.topics[topic_id].last_updated = time.time()
            return True
        return False
    
    def get_all_topics(self) -> List[Dict]:
        """获取所有话题信息"""
        return [topic.to_dict() for topic in self.topics.values()]
    
    def cleanup_old_topics(self, max_age_hours: int = 24) -> int:
        """清理旧话题"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        topics_to_remove = []
        for topic_id, topic in self.topics.items():
            if topic.last_updated < cutoff_time:
                topics_to_remove.append(topic_id)
        
        for topic_id in topics_to_remove:
            del self.topics[topic_id]
            
        return len(topics_to_remove)
    
    # 私有方法
    def _get_oldest_topic(self) -> Optional[Topic]:
        """获取最旧的话题"""
        if not self.topics:
            return None
        return min(self.topics.values(), key=lambda t: t.created_at)
    
    def _should_summarize(self, topic: Topic) -> bool:
        """判断是否需要生成摘要"""
        # 简单规则：消息数量超过5条或token数量超过1500
        return len(topic.messages) >= 5 or topic.token_count >= 1500
    
    def _generate_topic_summary(self, topic_id: str):
        """生成话题摘要（简化版本）"""
        if topic_id not in self.topics:
            return
            
        topic = self.topics[topic_id]
        
        # 简单的摘要生成逻辑
        if len(topic.messages) >= 5:
            # 取前3条和后2条消息作为摘要
            summary_messages = topic.messages[:3] + topic.messages[-2:]
            summary_content = "对话摘要：\n"
            for msg in summary_messages:
                summary_content += f"{msg.role}: {msg.content[:100]}...\n"
            
            topic.summary = summary_content.strip()
            topic.token_count = len(summary_content) * 1.3  # 更新token计数
    
    def _truncate_context(self, topic: Topic, max_tokens: int) -> Dict:
        """截断上下文以符合token限制"""
        # 简单的截断策略：保留最近的对话
        truncated_messages = []
        current_tokens = 0
        
        # 从后往前添加消息，直到达到token限制
        for message in reversed(topic.messages):
            message_tokens = len(message.content) * 1.3
            if current_tokens + message_tokens <= max_tokens:
                truncated_messages.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        return {
            "messages": [msg.to_dict() for msg in truncated_messages],
            "summary": topic.summary,
            "token_count": current_tokens,
            "topic_id": topic.topic_id,
            "truncated": True
        }
    
    def _cleanup_old_topic(self, topic_id: str):
        """清理旧话题数据"""
        if topic_id in self.topics:
            # 保留摘要，清理详细消息
            topic = self.topics[topic_id]
            topic.messages = []
            topic.token_count = 0
            topic.last_updated = time.time()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_topics = len(self.topics)
        total_tokens = sum(topic.token_count for topic in self.topics.values())
        total_messages = sum(len(topic.messages) for topic in self.topics.values())
        
        return {
            "total_topics": total_topics,
            "max_topics": self.max_topics,
            "total_tokens": total_tokens,
            "total_messages": total_messages,
            "current_topic": self.current_topic_id
        }