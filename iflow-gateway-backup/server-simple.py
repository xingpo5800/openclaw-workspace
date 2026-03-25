#!/usr/bin/env python3
"""
简化版 OpenClaw iFlow 网关服务器
专注于核心聊天功能，确保基本可用
"""

import os
import sys
import json
import time
import logging

# Flask 相关导入
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# iFlow SDK 导入
try:
    from iflow_sdk import query_sync, IFlowOptions
except ImportError:
    print("❌ iFlow SDK 未安装")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
HTTP_PORT = 8086
IFLOW_PORT = 8090
TIMEOUT = 60

# iFlow 配置
iflow_options = IFlowOptions(
    url=f"ws://127.0.0.1:{IFLOW_PORT}/acp",
    timeout=TIMEOUT,
    log_level="INFO"
)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'version': 'simple-1.0.0',
        'timestamp': time.time(),
        'http_port': HTTP_PORT,
        'iflow_port': IFLOW_PORT
    })

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
        }
    ]
    return jsonify({
        'object': 'list',
        'data': models
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """聊天 completions 接口 - 核心功能"""
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
                user_message = msg.get('content', '')
                break
        
        if not user_message:
            return jsonify({'error': 'No user message found'}), 400
        
        # 获取参数
        model = data.get('model', 'default')
        stream = data.get('stream', False)
        topic_id = data.get('topic_id', None)
        user_id = data.get('user_id', 'default')
        
        logger.info(f"📥 收到请求: model={model}, stream={stream}, topic_id={topic_id}")
        logger.info(f"📝 用户消息: {user_message[:50]}...")
        
        if stream:
            # 流式处理
            def generate_stream():
                # 先发送初始chunk
                init_chunk = {
                    'id': f'simple_{topic_id}_{int(time.time())}',
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': model,
                    'choices': [{
                        'index': 0,
                        'delta': {'role': 'assistant'},
                        'finish_reason': None
                    }]
                }
                yield f"data: {json.dumps(init_chunk, ensure_ascii=False)}\n\n"
                
                try:
                    # 调用 iFlow
                    response = query_sync(user_message, options=iflow_options)
                    logger.info(f"✅ iFlow 响应成功: {len(response)} 字符")
                    
                    # 分块发送响应
                    chunk_size = 50
                    for i in range(0, len(response), chunk_size):
                        chunk = response[i:i + chunk_size]
                        chunk_data = {
                            'id': f'simple_{topic_id}_{int(time.time())}',
                            'object': 'chat.completion.chunk',
                            'created': int(time.time()),
                            'model': model,
                            'choices': [{
                                'index': 0,
                                'delta': {'content': chunk},
                                'finish_reason': None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        time.sleep(0.01)
                    
                    # 发送结束标记
                    final_chunk = {
                        'id': f'simple_{topic_id}_{int(time.time())}',
                        'object': 'chat.completion.chunk',
                        'created': int(time.time()),
                        'model': model,
                        'choices': [{
                            'index': 0,
                            'delta': {},
                            'finish_reason': 'stop'
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"❌ iFlow 调用失败: {e}")
                    error_chunk = {
                        'id': f'error_{int(time.time())}',
                        'object': 'chat.completion.chunk',
                        'created': int(time.time()),
                        'model': model,
                        'choices': [{
                            'index': 0,
                            'delta': {'content': f"\n\n⚠️ 错误: {str(e)}"},
                            'finish_reason': 'stop'
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return Response(
                generate_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
            )
            
        else:
            # 非流式处理
            try:
                logger.info("🤖 调用 iFlow API...")
                response = query_sync(user_message, options=iflow_options)
                logger.info(f"✅ iFlow 响应成功: {len(response)} 字符")
                
                result = {
                    "topic_id": topic_id,
                    "response": response,
                    "timestamp": time.time(),
                    "context_info": {
                        "model": model,
                        "user_id": user_id
                    },
                    "from_cache": False
                }
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"❌ iFlow 调用失败: {e}")
                return jsonify({
                    'error': {
                        'type': 'processing_error',
                        'message': str(e)
                    }
                }), 500
            
    except Exception as e:
        logger.error(f"❌ 服务器错误: {e}")
        return jsonify({
            'error': {
                'type': 'server_error',
                'message': str(e)
            }
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 简化版 OpenClaw iFlow 网关服务器")
    print("=" * 50)
    print(f"📋 HTTP 端口: {HTTP_PORT}")
    print(f"🔌 iFlow ACP 端口: {IFLOW_PORT}")
    print("")
    print("✅ 核心功能：聊天")
    print("🎯 目标：确保基本可用")
    print("=" * 50)
    print("")
    
    try:
        app.run(host='0.0.0.0', port=HTTP_PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 服务器正在停止...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)