"""
智能话题摘要器
为对话话题生成摘要，减少上下文长度
"""

import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import Counter
import hashlib

@dataclass
class SummaryConfig:
    """摘要配置"""
    max_summary_length: int = 500  # 最大摘要长度
    min_messages_for_summary: int = 3  # 最少消息数才生成摘要
    summary_keywords: List[str] = None
    exclude_patterns: List[str] = None
    
    def __post_init__(self):
        if self.summary_keywords is None:
            self.summary_keywords = ["讨论", "问题", "解决", "方法", "步骤", "建议"]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                r"\b\d{4}-\d{2}-\d{2}\b",  # 日期
                r"\b\d{1,2}:\d{2}:\d{2}\b",  # 时间
                r"[\u4e00-\u9fff]{20,}"  # 过长的中文文本
            ]

class TopicSummarizer:
    """智能话题摘要器"""
    
    def __init__(self, config: SummaryConfig = None):
        self.config = config or SummaryConfig()
        
    def should_summarize(self, messages: List[Dict]) -> bool:
        """判断是否应该生成摘要"""
        if len(messages) < self.config.min_messages_for_summary:
            return False
        
        # 检查消息总长度
        total_length = sum(len(msg.get("content", "")) for msg in messages)
        return total_length > 1000  # 超过1000字符才考虑摘要
    
    def generate_summary(self, messages: List[Dict], existing_summary: str = "") -> str:
        """生成话题摘要"""
        if not messages:
            return existing_summary
        
        # 提取关键信息
        key_points = self._extract_key_points(messages)
        
        # 生成结构化摘要
        summary = self._build_structured_summary(key_points, existing_summary)
        
        # 确保摘要长度不超过限制
        return self._ensure_length_limit(summary)
    
    def _extract_key_points(self, messages: List[Dict]) -> Dict:
        """提取关键信息点"""
        key_points = {
            "topics": [],
            "questions": [],
            "solutions": [],
            "key_terms": [],
            "sentiment": "neutral"
        }
        
        content = ""
        for msg in messages:
            msg_content = msg.get("content", "")
            content += msg_content + " "
            
            # 提取问题
            questions = self._extract_questions(msg_content)
            key_points["questions"].extend(questions)
            
            # 提取解决方案
            solutions = self._extract_solutions(msg_content)
            key_points["solutions"].extend(solutions)
            
            # 提取关键术语
            terms = self._extract_key_terms(msg_content)
            key_points["key_terms"].extend(terms)
        
        # 提取主题
        topics = self._extract_topics(content)
        key_points["topics"] = topics
        
        # 分析情感
        key_points["sentiment"] = self._analyze_sentiment(content)
        
        return key_points
    
    def _extract_questions(self, text: str) -> List[str]:
        """提取问题"""
        questions = []
        # 匹配问号结尾的句子
        question_patterns = [
            r"[？?][^\n]*",
            r"怎么[^\n]*",
            r"如何[^\n]*",
            r"为什么[^\n]*",
            r"什么是[^\n]*",
            r"如何[^\n]*"
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, text)
            questions.extend(matches[:2])  # 最多取2个问题
        
        return questions
    
    def _extract_solutions(self, text: str) -> List[str]:
        """提取解决方案"""
        solutions = []
        solution_patterns = [
            r"解决[^\n。！？]{10,50}",
            r"方法[^\n。！？]{10,50}",
            r"建议[^\n。！？]{10,50}",
            r"步骤[^\n。！？]{10,50}",
            r"应该[^\n。！？]{10,50}"
        ]
        
        for pattern in solution_patterns:
            matches = re.findall(pattern, text)
            solutions.extend(matches[:2])  # 最多取2个解决方案
        
        return solutions
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """提取关键术语"""
        terms = []
        
        # 移除排除模式
        for pattern in self.config.exclude_patterns:
            text = re.sub(pattern, "", text)
        
        # 提取中文关键词（2-4个字符）
        chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
        
        # 统计词频，取高频词
        term_counter = Counter(chinese_terms)
        for term, count in term_counter.most_common(10):
            if count >= 2:  # 至少出现2次
                terms.append(term)
        
        return terms
    
    def _extract_topics(self, text: str) -> List[str]:
        """提取主题"""
        topics = []
        
        # 基于关键词匹配主题
        for keyword in self.config.summary_keywords:
            if keyword in text:
                topics.append(keyword)
        
        # 去重
        return list(set(topics))
    
    def _analyze_sentiment(self, text: str) -> str:
        """简单情感分析"""
        positive_words = ["好", "棒", "成功", "正确", "满意", "不错"]
        negative_words = ["问题", "错误", "失败", "困难", "不好", "糟糕"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _build_structured_summary(self, key_points: Dict, existing_summary: str = "") -> str:
        """构建结构化摘要"""
        summary_parts = []
        
        # 如果有现有摘要，保留部分信息
        if existing_summary:
            summary_parts.append(f"前次摘要: {existing_summary[:100]}...")
        
        # 添加主题
        if key_points["topics"]:
            summary_parts.append(f"主要主题: {', '.join(key_points['topics'])}")
        
        # 添加关键问题
        if key_points["questions"]:
            summary_parts.append(f"关键问题: {'; '.join(key_points['questions'][:2])}")
        
        # 添加解决方案
        if key_points["solutions"]:
            summary_parts.append(f"解决方案: {'; '.join(key_points['solutions'][:2])}")
        
        # 添加关键术语
        if key_points["key_terms"]:
            summary_parts.append(f"关键词: {', '.join(key_points['key_terms'][:5])}")
        
        # 添加情感分析
        sentiment = key_points["sentiment"]
        sentiment_text = {"positive": "积极", "negative": "消极", "neutral": "中性"}
        summary_parts.append(f"对话情感: {sentiment_text.get(sentiment, '未知')}")
        
        return " | ".join(summary_parts)
    
    def _ensure_length_limit(self, summary: str) -> str:
        """确保摘要长度不超过限制"""
        if len(summary) <= self.config.max_summary_length:
            return summary
        
        # 如果超长，截断并添加省略号
        return summary[:self.config.max_summary_length - 3] + "..."
    
    def incremental_summary(self, messages: List[Dict], current_summary: str, new_message: str) -> str:
        """增量更新摘要"""
        # 将新消息添加到消息列表
        updated_messages = messages + [{"content": new_message}]
        
        # 生成新的摘要
        new_summary = self.generate_summary(updated_messages, current_summary)
        
        return new_summary
    
    def get_summary_quality(self, summary: str, original_messages: List[Dict]) -> Dict:
        """评估摘要质量"""
        original_length = sum(len(msg.get("content", "")) for msg in original_messages)
        summary_length = len(summary)
        
        compression_ratio = summary_length / original_length if original_length > 0 else 0
        
        # 简单的质量评估
        quality_score = 0
        
        # 压缩比评分 (0-25分)
        if 0.1 <= compression_ratio <= 0.3:
            quality_score += 20
        elif 0.05 <= compression_ratio < 0.1 or 0.3 < compression_ratio <= 0.5:
            quality_score += 10
        
        # 摘要长度评分 (0-25分)
        if 100 <= summary_length <= 500:
            quality_score += 20
        elif 50 <= summary_length < 100 or 500 < summary_length <= 800:
            quality_score += 10
        
        # 信息完整性评分 (0-50分)
        has_topics = any("主题" in summary for _ in range(1))
        has_questions = any("问题" in summary for _ in range(1))
        has_solutions = any("解决" in summary for _ in range(1))
        
        if has_topics:
            quality_score += 15
        if has_questions:
            quality_score += 15
        if has_solutions:
            quality_score += 20
        
        return {
            "quality_score": quality_score,
            "compression_ratio": compression_ratio,
            "original_length": original_length,
            "summary_length": summary_length,
            "has_topics": has_topics,
            "has_questions": has_questions,
            "has_solutions": has_solutions
        }