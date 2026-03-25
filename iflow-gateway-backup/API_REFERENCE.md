# OpenClaw iFlow Gateway API 接口文档

## 📡 API 概览

OpenClaw iFlow Gateway 提供兼容 OpenAI API 的 HTTP 接口，支持多种 iFlow 模型的调用。

### 基本信息
- **Base URL**: `http://127.0.0.1:8086/v1`
- **协议**: HTTP/HTTPS
- **认证方式**: Bearer Token
- **Content-Type**: `application/json`

### 认证
```bash
Authorization: Bearer sk-7f2c30fe73e680c15527e4a6dfb5d55e
```

## 📋 API 端点

### 1. 健康检查

#### GET /health
检查服务健康状态。

**请求示例**:
```bash
curl http://127.0.0.1:8086/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "simple-1.0.0",
  "timestamp": 1774032894.306219,
  "http_port": 8086,
  "iflow_port": 8090,
  "features": [
    "智能上下文管理",
    "响应缓存",
    "话题摘要",
    "智能分块",
    "性能监控"
  ]
}
```

**响应字段**:
- `status`: 服务状态 (healthy/unhealthy)
- `version`: 服务版本
- `timestamp`: 时间戳
- `http_port`: HTTP 服务端口
- `iflow_port`: iFlow ACP 端口
- `features`: 支持的功能列表

### 2. 服务状态

#### GET /status
获取服务运行状态。

**请求示例**:
```bash
curl http://127.0.0.1:8086/status
```

**响应示例**:
```json
{
  "status": "running",
  "iflow_connected": true,
  "version": "1.0.0",
  "timestamp": 1774032894.306219,
  "iflow_port": 8090,
  "http_port": 8086
}
```

**响应字段**:
- `status`: 服务状态
- `iflow_connected`: iFlow 连接状态
- `version`: 服务版本
- `timestamp`: 时间戳
- `http_port`: HTTP 服务端口
- `iflow_port`: iFlow ACP 端口

### 3. 统计信息

#### GET /gateway/stats
获取网关运行统计信息（仅完整版服务器支持）。

**请求示例**:
```bash
curl http://127.0.0.1:8086/gateway/stats
```

**响应示例**:
```json
{
  "gateway_stats": {
    "total_requests": 150,
    "cache_hits": 45,
    "cache_misses": 105,
    "total_tokens_processed": 45678,
    "avg_response_time": 2.34,
    "errors": 2
  },
  "cache_stats": {
    "cache_size": 156,
    "max_size": 1000,
    "hit_rate": "30.00%"
  },
  "config": {
    "max_topics": 5,
    "max_tokens_per_topic": 2000,
    "max_cache_size": 1000
  }
}
```

**响应字段**:
- `gateway_stats`: 网关统计信息
  - `total_requests`: 总请求数
  - `cache_hits`: 缓存命中次数
  - `cache_misses`: 缓存未命中次数
  - `total_tokens_processed`: 处理的 Token 总数
  - `avg_response_time`: 平均响应时间（秒）
  - `errors`: 错误次数
- `cache_stats`: 缓存统计信息
  - `cache_size`: 当前缓存大小
  - `max_size`: 最大缓存大小
  - `hit_rate`: 缓存命中率
- `config`: 当前配置信息

### 4. 模型列表

#### GET /v1/models
获取可用的模型列表。

**请求示例**:
```bash
curl http://127.0.0.1:8086/v1/models
```

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "kimi-k2.5",
      "object": "model",
      "created": 1774032894,
      "owned_by": "iflow",
      "name": "灵犀",
      "description": "月之暗面 Kimi K2.5"
    },
    {
      "id": "glm-4.7",
      "object": "model",
      "created": 1774032894,
      "owned_by": "iflow",
      "name": "灵犀",
      "description": "智谱 GLM-4.7"
    },
    {
      "id": "glm-5",
      "object": "model",
      "created": 1774032894,
      "owned_by": "iflow",
      "name": "灵犀",
      "description": "智谱 GLM-5"
    },
    {
      "id": "qwen3-coder-plus",
      "object": "model",
      "created": 1774032894,
      "owned_by": "iflow",
      "name": "灵犀",
      "description": "通义千问 Qwen3 Coder Plus"
    }
  ]
}
```

**响应字段**:
- `object`: 对象类型 (list)
- `data`: 模型列表
  - `id`: 模型唯一标识符
  - `object`: 对象类型 (model)
  - `created`: 创建时间戳
  - `owned_by`: 拥有者
  - `name`: 模型名称
  - `description`: 模型描述

### 5. 聊天完成

#### POST /v1/chat/completions
发送聊天请求并获取模型响应。

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-7f2c30fe73e680c15527e4a6dfb5d55e" \
  -d '{
    "model": "kimi-k2.5",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": false,
    "topic_id": "optional-topic-id",
    "user_id": "optional-user-id"
  }'
```

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `model` | string | 是 | 要使用的模型 ID |
| `messages` | array | 是 | 消息列表 |
| `temperature` | float | 否 | 温度参数 (0.0-2.0) |
| `max_tokens` | integer | 否 | 最大输出 Token 数 |
| `stream` | boolean | 否 | 是否流式响应 |
| `topic_id` | string | 否 | 话题 ID (用于上下文管理) |
| `user_id` | string | 否 | 用户 ID (用于会话隔离) |

**消息格式**:
```json
{
  "messages": [
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "助手回复"},
    {"role": "user", "content": "用户的新消息"}
  ]
}
```

**响应示例 (非流式)**:
```json
{
  "topic_id": "abc123def456",
  "response": "你好！我是灵犀，一个由 iFlow 提供支持的 AI 助手。我可以回答问题、提供信息、帮助解决问题，并进行自然对话。有什么我可以帮助你的吗？",
  "timestamp": 1774032894.306219,
  "context_info": {
    "model": "kimi-k2.5",
    "user_id": "default",
    "token_count": 156,
    "messages_count": 1,
    "has_summary": false,
    "truncated": false
  },
  "from_cache": false
}
```

**响应字段**:
- `topic_id`: 话题 ID
- `response`: 模型回复内容
- `timestamp`: 响应时间戳
- `context_info`: 上下文信息
  - `model`: 使用的模型
  - `user_id`: 用户 ID
  - `token_count`: Token 数量
  - `messages_count`: 消息数量
  - `has_summary`: 是否有摘要
  - `truncated`: 是否被截断
- `from_cache`: 是否来自缓存

### 6. 流式聊天

#### POST /v1/chat/completions (流式)
发送流式聊天请求。

**请求示例**:
```bash
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-7f2c30fe73e680c15527e4a6dfb5d55e" \
  -d '{
    "model": "kimi-k2.5",
    "messages": [
      {"role": "user", "content": "请详细介绍一下人工智能的发展历史"}
    ],
    "stream": true
  }'
```

**流式响应格式**:
```json
data: {"id":"simple_abc123_1774032894","object":"chat.completion.chunk","created":1774032894,"model":"kimi-k2.5","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"simple_abc123_1774032894","object":"chat.completion.chunk","created":1774032894,"model":"kimi-k2.5","choices":[{"index":0,"delta":{"content":"人工智能的发展历史可以追溯到..."},"finish_reason":null}]}

data: {"id":"simple_abc123_1774032894","object":"chat.completion.chunk","created":1774032894,"model":"kimi-k2.5","choices":[{"index":0,"delta":{"content":"从早期的符号逻辑到现代的深度学习..."},"finish_reason":null}]}

data: {"id":"simple_abc123_1774032894","object":"chat.completion.chunk","created":1774032894,"model":"kimi-k2.5","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**流式响应字段**:
- `id`: 响应 ID
- `object`: 对象类型 (chat.completion.chunk)
- `created`: 创建时间戳
- `model`: 使用的模型
- `choices`: 选择列表
  - `index`: 索引
  - `delta`: 增量内容
    - `role`: 角色信息
    - `content`: 内容增量
  - `finish_reason`: 完成原因

## 🚨 错误处理

### 错误响应格式
```json
{
  "error": {
    "type": "error_type",
    "message": "错误描述信息",
    "code": "error_code",
    "param": "参数名",
    "topic_id": "abc123"
  },
  "timestamp": 1774032894.306219
}
```

### 常见错误代码

| 错误代码 | HTTP 状态码 | 描述 |
|----------|-------------|------|
| `invalid_request` | 400 | 请求格式错误 |
| `authentication_error` | 401 | 认证失败 |
| `permission_error` | 403 | 权限不足 |
| `not_found` | 404 | 资源不存在 |
| `rate_limit_error` | 429 | 请求频率超限 |
| `server_error` | 500 | 服务器内部错误 |
| `processing_error` | 502 | 处理错误 |

### 错误示例

#### 1. 认证错误
```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid API key",
    "code": "invalid_api_key"
  },
  "timestamp": 1774032894.306219
}
```

#### 2. 模型不存在
```json
{
  "error": {
    "type": "not_found",
    "message": "Model not found",
    "code": "model_not_found",
    "param": "model"
  },
  "timestamp": 1774032894.306219
}
```

#### 3. 处理错误
```json
{
  "error": {
    "type": "processing_error",
    "message": "iFlow processing timeout",
    "code": "processing_timeout",
    "topic_id": "abc123"
  },
  "timestamp": 1774032894.306219
}
```

## 📊 限制和配额

### 请求限制
- **最大请求大小**: 16MB
- **最大响应大小**: 无限制（流式响应）
- **并发连接数**: 100
- **每分钟请求数**: 1000

### Token 限制
- **上下文窗口**: 128K-204K（取决于模型）
- **最大输出 Token**: 32K-131K（取决于模型）
- **单次请求最大 Token**: 128K

## 🔄 WebSocket 接口

### iFlow ACP WebSocket
**地址**: `ws://127.0.0.1:8090/acp`

**协议**: 自定义 ACP 协议
- **握手**: `//ready`
- **认证**: `authenticate`
- **会话管理**: `session/new`, `session/close`
- **消息处理**: `session/prompt`

**使用示例**:
```javascript
const ws = new WebSocket('ws://127.0.0.1:8090/acp');

ws.onopen = () => {
  console.log('Connected to iFlow ACP');
  
  // 发送认证
  ws.send(JSON.stringify({
    method: 'authenticate',
    params: {
      method: 'iflow'
    }
  }));
  
  // 创建会话
  ws.send(JSON.stringify({
    method: 'session/new',
    params: {
      cwd: '/path/to/project'
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

**API 接口文档完成**  
**最后更新**: 2026-03-21