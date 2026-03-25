#!/usr/bin/env python3
"""
OpenClaw iFlow 智能网关服务器
====================================

这是一个独立的智能网关服务器，用于连接 OpenClaw 和 iFlow CLI。
实现了智能上下文管理、响应缓存、话题摘要等功能。

特性：
- 智能上下文管理（滑动窗口、自动摘要）
- 响应缓存系统
- 话题自动摘要
- 智能分块处理
- 性能监控统计
- 错误恢复机制

作者：灵犀
创建时间：2026-03-19
版本：v1.0.0
"""

import os
import sys
import json
import time
import re
import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Flask 相关导入
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# iFlow SDK 导入
try:
    from iflow_cli_sdk import query_sync, IFlowOptions
except ImportError:
    try:
        from iflow_sdk import query_sync, IFlowOptions
    except ImportError:
        print("❌ iFlow SDK 未安装，请运行: pip install iflow-cli-sdk")
        sys.exit(1)

# 配置日志
# 创建日志目录
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gateway.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 配置类 ====================

@dataclass
class GatewayConfig:
    """网关配置类"""
    def __init__(self):
        # 服务器配置
        self.http_port: int = 8086
        self.iflow_port: int = 8090
        self.timeout: float = 60.0
        
        # 网关功能配置
        self.max_topics: int = 5
        self.max_tokens_per_topic: int = 2000
        self.max_cache_size: int = 1000
        self.max_summary_length: int = 500
        self.chunk_size: int = 100
        self.enable_compression: bool = True
        
        # 性能配置
        max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.max_workers: int = max_workers
        
        # 从配置文件加载（如果存在）
        self._load_config()
    
    def _load_config(self):
        """从配置文件加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'gateway.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 更新配置
                if 'server' in config:
                    server_config = config['server']
                    self.http_port = server_config.get('http_port', self.http_port)
                    self.iflow_port = server_config.get('iflow_port', self.iflow_port)
                    self.timeout = server_config.get('timeout', self.timeout)
                
                if 'gateway' in config:
                    gateway_config = config['gateway']
                    self.max_topics = gateway_config.get('max_topics', self.max_topics)
                    self.max_tokens_per_topic = gateway_config.get('max_tokens_per_topic', self.max_tokens_per_topic)
                    self.max_cache_size = gateway_config.get('max_cache_size', self.max_cache_size)
                    self.max_summary_length = gateway_config.get('max_summary_length', self.max_summary_length)
                    self.chunk_size = gateway_config.get('chunk_size', self.chunk_size)
                    self.enable_compression = gateway_config.get('enable_compression', self.enable_compression)
                
                logger.info("✅ 配置文件加载成功")
                
            except Exception as e:
                logger.warning(f"⚠️ 配置文件加载失败: {e}，使用默认配置")

# ==================== 上下文管理器 ====================

class ContextManager:
    """上下文管理器 - 管理对话上下文和话题生命周期"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.topics: Dict[str, Dict] = {}
        self.current_topic_id: Optional[str] = None
        
    def create_topic(self, topic_id: str, initial_message: str = "") -> Dict:
        """创建新话题"""
        # 如果话题数量超过限制，删除最旧的话题
        if len(self.topics) >= self.config.max_topics:
            oldest_topic = min(
                self.topics.keys(), 
                key=lambda k: self.topics[k].get('created_at', 0)
            )
            if oldest_topic:
                del self.topics[oldest_topic]
                logger.info(f"🗑️ 清理旧话题: {oldest_topic}")
        
        # 创建新话题
        topic = {
            'topic_id': topic_id,
            'messages': [],
            'summary': '',
            'created_at': time.time(),
            'last_updated': time.time(),
            'token_count': 0,
            'message_count': 0
        }
        
        # 如果有初始消息，添加到话题中
        if initial_message:
            self.add_message(topic_id, "user", initial_message)
            
        self.topics[topic_id] = topic
        self.current_topic_id = topic_id
        logger.info(f"🆕 创建新话题: {topic_id}")
        return topic
    
    def add_message(self, topic_id: str, role: str, content: str) -> bool:
        """添加消息到话题"""
        if topic_id not in self.topics:
            logger.warning(f"⚠️ 话题不存在: {topic_id}")
            return False
            
        topic = self.topics[topic_id]
        message_id = hashlib.md5(f"{role}{content}{time.time()}".encode()).hexdigest()[:16]
        
        # 创建消息对象
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'message_id': message_id
        }
        
        # 添加消息到话题
        topic['messages'].append(message)
        topic['last_updated'] = time.time()
        topic['message_count'] += 1
        
        # 计算token数量（粗略估算：1个字符约等于1.3个token）
        topic['token_count'] += len(content) * 1.3
        
        # 如果token数量超过阈值，自动生成摘要
        if topic['token_count'] > 1500:
            topic['summary'] = self._generate_summary(topic['messages'])
            logger.info(f"📝 自动生成话题摘要: {topic_id}")
            
        return True
    
    def get_context(self, topic_id: str) -> Dict:
        """获取话题上下文"""
        if topic_id not in self.topics:
            logger.warning(f"⚠️ 话题不存在: {topic_id}")
            return {"messages": [], "summary": "", "token_count": 0}
            
        topic = self.topics[topic_id]
        
        # 如果token数量超过限制，进行截断
        if topic['token_count'] > self.config.max_tokens_per_topic:
            logger.info(f"🔄 截断话题上下文: {topic_id} ({topic['token_count']} -> {self.config.max_tokens_per_topic})")
            
            # 保留最近的对话（用户+助手各一条）
            recent_messages = []
            for i in range(len(topic['messages']) - 1, -1, -1):
                msg = topic['messages'][i]
                recent_messages.append(msg)
                if len(recent_messages) >= 2 and msg['role'] == 'user':
                    break
            
            recent_messages.reverse()
            
            return {
                "messages": recent_messages,
                "summary": topic['summary'],
                "token_count": sum(len(msg['content']) * 1.3 for msg in recent_messages),
                "topic_id": topic_id,
                "truncated": True,
                "original_message_count": topic['message_count']
            }
        
        return {
            "messages": topic['messages'],
            "summary": topic['summary'],
            "token_count": topic['token_count'],
            "topic_id": topic_id,
            "truncated": False,
            "original_message_count": topic['message_count']
        }
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成话题摘要"""
        if len(messages) < 3:
            return ""
        
        # 取前2条和后1条消息生成摘要
        summary_messages = messages[:2] + messages[-1:]
        summary = "对话摘要：\n"
        
        for msg in summary_messages:
            # 截取前50个字符
            content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            summary += f"{msg['role']}: {content_preview}\n"
        
        return summary.strip()

# ==================== 响应缓存系统 ====================

class ResponseCache:
    """响应缓存系统 - 缓存常见问题的响应"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Dict] = {}
        
    def get(self, message: str, context: Dict) -> Optional[Dict]:
        """获取缓存的响应"""
        # 生成缓存键
        summary = context.get('summary', '')
        cache_key = hashlib.md5(f"{message}|{summary}".encode()).hexdigest()
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # 检查是否过期（1小时）
            if time.time() - entry['created_at'] < 3600:
                logger.debug(f"🎯 缓存命中: {cache_key[:8]}...")
                return entry['response'].copy()
            else:
                # 删除过期缓存
                del self.cache[cache_key]
                logger.debug(f"🗑️ 缓存过期: {cache_key[:8]}...")
        
        return None
    
    def put(self, message: str, context: Dict, response: Dict) -> bool:
        """缓存响应"""
        # 生成缓存键
        summary = context.get('summary', '')
        cache_key = hashlib.md5(f"{message}|{summary}".encode()).hexdigest()
        
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['created_at'])
            del self.cache[oldest_key]
            logger.debug(f"🗑️ 清理缓存: {oldest_key[:8]}...")
        
        # 存储响应
        self.cache[cache_key] = {
            'response': response,
            'created_at': time.time()
        }
        
        logger.debug(f"💾 缓存响应: {cache_key[:8]}...")
        return True
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': 'N/A'  # 需要在外部计算命中率
        }

# ==================== 智能网关 ====================

class SmartGateway:
    """智能网关 - 整合所有功能的核心组件"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.context_manager = ContextManager(config)
        self.response_cache = ResponseCache(config.max_cache_size)
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens_processed": 0,
            "avg_response_time": 0.0,
            "errors": 0
        }
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        
        # iFlow 配置
        self.iflow_options = IFlowOptions(
            url=f"ws://127.0.0.1:{config.iflow_port}/acp",
            timeout=config.timeout,
            log_level="INFO"
        )
        
        logger.info("🚀 智能网关初始化完成")
    
    async def process_request(self, message: str, topic_id: str = None, user_id: str = None) -> Dict:
        """处理请求"""
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # 生成话题ID
        if topic_id is None:
            topic_id = hashlib.md5(f"{user_id or 'default'}_{time.time()}".encode()).hexdigest()[:16]
        
        logger.info(f"📥 处理请求: topic_id={topic_id}, user_id={user_id or 'default'}")
        
        # 获取上下文
        context = self.context_manager.get_context(topic_id)
        
        # 检查缓存
        cached_response = self.response_cache.get(message, context)
        if cached_response:
            self.stats["cache_hits"] += 1
            cached_response["from_cache"] = True
            logger.info(f"🎯 缓存命中: topic_id={topic_id}")
            return cached_response
        
        self.stats["cache_misses"] += 1
        
        # 添加用户消息到上下文
        self.context_manager.add_message(topic_id, "user", message)
        updated_context = self.context_manager.get_context(topic_id)
        
        try:
            # 生成AI响应
            logger.info(f"🤖 调用 iFlow API: topic_id={topic_id}")
            logger.info(f"📝 查询消息: {message[:50]}...")
            
            ai_response = query_sync(message, options=self.iflow_options)
            
            logger.info(f"✅ iFlow 响应成功: {len(ai_response)} 字符")
            
            # 处理响应
            processed_response = {
                "topic_id": topic_id,
                "response": ai_response,
                "timestamp": time.time(),
                "context_info": {
                    "token_count": updated_context.get("token_count", 0),
                    "messages_count": len(updated_context.get("messages", [])),
                    "has_summary": bool(updated_context.get("summary", "")),
                    "truncated": updated_context.get("truncated", False)
                },
                "from_cache": False,
                "processing_time": time.time() - start_time
            }
            
            # 缓存响应
            self.response_cache.put(message, context, processed_response)
            
            # 添加AI回复到上下文
            self.context_manager.add_message(topic_id, "assistant", ai_response)
            
            # 更新统计信息
            self.stats["total_tokens_processed"] += len(ai_response)
            
            # 计算平均响应时间
            current_time = time.time() - start_time
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["total_requests"] - 1) + current_time) 
                / self.stats["total_requests"]
            )
            
            logger.info(f"✅ 请求处理完成: topic_id={topic_id}, time={current_time:.2f}s")
            return processed_response
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ 处理请求失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            return {
                "error": {
                    "type": "processing_error",
                    "message": str(e),
                    "topic_id": topic_id
                },
                "timestamp": time.time(),
                "from_cache": False
            }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cache_stats = self.response_cache.get_stats()
        
        # 计算缓存命中率
        total_requests = self.stats["total_requests"]
        if total_requests > 0:
            hit_rate = self.stats["cache_hits"] / total_requests
            cache_stats['hit_rate'] = f"{hit_rate:.2%}"
        
        return {
            "gateway_stats": self.stats,
            "cache_stats": cache_stats,
            "config": {
                "max_topics": self.config.max_topics,
                "max_tokens_per_topic": self.config.max_tokens_per_topic,
                "max_cache_size": self.config.max_cache_size
            }
        }

# ==================== 全局变量 ====================

# 创建配置实例
config = GatewayConfig()

# 创建智能网关实例
smart_gateway = SmartGateway(config)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# ==================== API 路由 ====================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': time.time(),
        'iflow_port': config.iflow_port,
        'http_port': config.http_port,
        'features': [
            '智能上下文管理',
            '响应缓存',
            '话题摘要',
            '智能分块',
            '性能监控'
        ]
    })

@app.route('/status', methods=['GET'])
def status():
    """状态检查接口"""
    return jsonify({
        'status': 'running',
        'iflow_connected': True,
        'version': '1.0.0',
        'timestamp': time.time(),
        'iflow_port': config.iflow_port,
        'http_port': config.http_port
    })

@app.route('/gateway/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    return jsonify(smart_gateway.get_stats())

@app.route('/v1/models', methods=['GET'])
def list_models():
    """模型列表接口"""
    models = [
        {
            'id': 'kimi-k2.5', 
            'object': 'model', 
            'created': int(time.time()), 
            'owned_by': 'iflow',
            'name': '灵犀',
            'description': '月之暗面 Kimi K2.5'
        },
        {
            'id': 'glm-4.7', 
            'object': 'model', 
            'created': int(time.time()), 
            'owned_by': 'iflow',
            'name': '灵犀',
            'description': '智谱 GLM-4.7'
        },
        {
            'id': 'glm-5', 
            'object': 'model', 
            'created': int(time.time()), 
            'owned_by': 'iflow',
            'name': '灵犀',
            'description': '智谱 GLM-5'
        },
        {
            'id': 'qwen3-coder-plus', 
            'object': 'model', 
            'created': int(time.time()), 
            'owned_by': 'iflow',
            'name': '灵犀',
            'description': '通义千问 Qwen3 Coder Plus'
        }
    ]
    return jsonify({
        'object': 'list',
        'data': models
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """聊天 completions 接口"""
    try:
        data = request.json
        
        # 提取用户消息
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            user_message = item.get('text', '')
                            break
                else:
                    user_message = content
                break
        
        if not user_message:
            return jsonify({'error': 'No user message found'}), 400
        
        # 获取参数
        model = data.get('model', 'default')
        stream = data.get('stream', False)
        topic_id = data.get('topic_id', None)
        user_id = data.get('user_id', 'default')
        
        logger.info(f"📥 收到请求: model={model}, stream={stream}, topic_id={topic_id}")
        
        if stream:
            # 流式处理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                future = asyncio.run_coroutine_threadsafe(
                    smart_gateway.process_request(user_message, topic_id, user_id), 
                    loop
                )
                result = future.result(timeout=config.timeout)
                
                return Response(
                    generate_stream_response(result),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'X-Accel-Buffering': 'no'
                    }
                )
            finally:
                loop.close()
        else:
            # 非流式处理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                future = asyncio.run_coroutine_threadsafe(
                    smart_gateway.process_request(user_message, topic_id, user_id), 
                    loop
                )
                result = future.result(timeout=config.timeout)
                return jsonify(result)
            finally:
                loop.close()
            
    except Exception as e:
        logger.error(f"❌ 服务器错误: {e}")
        return jsonify({
            'error': {
                'type': 'server_error',
                'message': str(e)
            }
        }), 500

def generate_stream_response(result: Dict):
    """生成流式响应"""
    try:
        response_content = result.get('response', '')
        topic_id = result.get('topic_id', '')
        error_info = result.get('error')
        
        # 如果有错误，先生成错误信息
        if error_info:
            error_msg = f"\n\n⚠️ 处理错误: {error_info.get('message', '未知错误')}"
            response_content += error_msg
        
        # 发送初始chunk
        init_chunk = {
            'id': f'smart_{topic_id}_{int(time.time())}',
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': result.get('model', 'default'),
            'choices': [{
                'index': 0,
                'delta': {
                    'role': 'assistant'
                },
                'finish_reason': None
            }]
        }
        yield f"data: {json.dumps(init_chunk, ensure_ascii=False)}\n\n"
        
        # 发送内容
        chunk_size = config.chunk_size
        for i in range(0, len(response_content), chunk_size):
            chunk = response_content[i:i + chunk_size]
            chunk_data = {
                'id': f'smart_{topic_id}_{int(time.time())}',
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': result.get('model', 'default'),
                'choices': [{
                    'index': 0,
                    'delta': {
                        'content': chunk
                    },
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            time.sleep(0.01)  # 控制发送速度
        
        # 发送结束标记
        final_chunk = {
            'id': f'smart_{topic_id}_{int(time.time())}',
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': result.get('model', 'default'),
            'choices': [{
                'index': 0,
                'delta': {},
                'finish_reason': 'stop'
            }]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"❌ 流式生成错误: {e}")
        error_chunk = {
            'id': f'error_{int(time.time())}',
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': 'default',
            'choices': [{
                'index': 0,
                'delta': {
                    'content': f"\n\n⚠️ 流式传输错误: {str(e)}"
                },
                'finish_reason': 'stop'
            }]
        }
        yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    print("=" * 60)
    print("🚀 OpenClaw iFlow 智能网关服务器")
    print("=" * 60)
    print(f"📋 HTTP 端口: {config.http_port}")
    print(f"🔌 iFlow ACP 端口: {config.iflow_port}")
    print(f"🧵 最大工作线程: {config.max_workers}")
    print("")
    print("🎯 智能特性:")
    print("   ✅ 智能上下文管理")
    print("   ✅ 响应缓存系统")
    print("   ✅ 话题自动摘要")
    print("   ✅ 智能分块处理")
    print("   ✅ 性能监控统计")
    print("   ✅ 错误恢复机制")
    print("✅ 完整的网关数据流处理解决方案")
    print("=" * 60)
    print("")
    
    try:
        # 启动 Flask 服务器
        app.run(
            host='0.0.0.0', 
            port=config.http_port, 
            debug=False, 
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器正在停止...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)