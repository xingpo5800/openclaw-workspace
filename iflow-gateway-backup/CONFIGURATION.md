# OpenClaw iFlow Gateway 配置说明

## 📐 配置文件结构

### 主要配置文件
- `config/gateway.json` - 网关核心配置
- `server.py` - 完整版服务器配置
- `server-simple.py` - 简化版服务器配置

## 🔧 网关配置 (config/gateway.json)

```json
{
  "server": {
    "http_port": 8086,
    "iflow_port": 8090,
    "timeout": 60
  },
  "gateway": {
    "max_topics": 5,
    "max_tokens_per_topic": 2000,
    "max_cache_size": 1000,
    "max_summary_length": 500,
    "chunk_size": 100,
    "enable_compression": true
  },
  "logging": {
    "level": "INFO",
    "file": "../logs/gateway.log"
  }
}
```

### 配置参数详解

#### 服务器配置 (server)
- **http_port**: HTTP API 服务端口 (默认: 8086)
- **iflow_port**: iFlow ACP WebSocket 端口 (默认: 8090)
- **timeout**: 请求超时时间，单位秒 (默认: 60)

#### 网关功能配置 (gateway)
- **max_topics**: 最大话题数量，超过自动清理旧话题 (默认: 5)
- **max_tokens_per_topic**: 单个话题最大 token 数量，超过自动截断 (默认: 2000)
- **max_cache_size**: 响应缓存最大条目数 (默认: 1000)
- **max_summary_length**: 话题摘要最大长度 (默认: 500)
- **chunk_size**: 流式响应分块大小 (默认: 100)
- **enable_compression**: 是否启用响应压缩 (默认: true)

#### 日志配置 (logging)
- **level**: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- **file**: 日志文件路径

## 🌐 OpenClaw 集成配置

### OpenClaw 配置文件 (openclaw.json)

```json
{
  "models": {
    "providers": {
      "iflow": {
        "baseUrl": "http://127.0.0.1:8086/v1",
        "apiKey": "sk-7f2c30fe73e680c15527e4a6dfb5d55e",
        "api": "openai-completions",
        "models": [
          {
            "id": "kimi-k2.5",
            "name": "Kimi-K2.5 (iFlow SDK)",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 128000,
            "maxTokens": 32768
          },
          {
            "id": "glm-4.7",
            "name": "GLM-4.7 (iFlow SDK)",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 204800,
            "maxTokens": 131072
          }
          // 更多模型...
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "iflow/kimi-k2.5",
        "fallbacks": [
          "iflow/glm-4.7",
          "iflow/glm-5",
          "iflow/qwen3-coder-plus"
        ]
      },
      "models": {
        "iflow/kimi-k2.5": {
          "alias": "kimi-2.5"
        },
        "iflow/glm-4.7": {
          "alias": "glm-4.7"
        }
      }
    }
  }
}
```

### 模型配置参数

#### 基础参数
- **id**: 模型唯一标识符
- **name**: 模型显示名称
- **reasoning**: 是否支持推理模式
- **input**: 输入类型 (["text"])
- **cost**: 成本配置 (input/output/cacheRead/cacheWrite)

#### 性能参数
- **contextWindow**: 上下文窗口大小
- **maxTokens**: 最大输出 token 数量

## 🔄 环境变量配置

### 可选环境变量
```bash
# 自定义端口
export IFLOW_HTTP_PORT=8086
export IFLOW_ACP_PORT=8090

# 自定义超时时间
export IFLOW_TIMEOUT=60

# 自定义日志级别
export IFLOW_LOG_LEVEL=INFO
```

## 📊 性能调优建议

### 高负载配置
```json
{
  "gateway": {
    "max_topics": 10,
    "max_tokens_per_topic": 4000,
    "max_cache_size": 2000,
    "chunk_size": 50,
    "enable_compression": true
  }
}
```

### 节省资源配置
```json
{
  "gateway": {
    "max_topics": 3,
    "max_tokens_per_topic": 1000,
    "max_cache_size": 500,
    "chunk_size": 200,
    "enable_compression": false
  }
}
```

## 🛠️ 配置验证

### 验证步骤
1. 检查配置文件语法
   ```bash
   python -m json.tool config/gateway.json
   ```

2. 测试配置加载
   ```bash
   python3 -c "
   import json
   with open('config/gateway.json', 'r') as f:
       config = json.load(f)
   print('配置加载成功:', config)
   "
   ```

3. 验证 OpenClaw 配置
   ```bash
   curl -X POST http://127.0.0.1:8086/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "kimi-k2.5", "messages": [{"role": "user", "content": "测试配置"}]}'
   ```

## 🔍 配置问题排查

### 常见配置错误

#### 1. 端口冲突
```bash
# 检查端口占用
lsof -i :8086
lsof -i :8090

# 修改配置文件中的端口
sed -i 's/"http_port": 8086/"http_port": 8087/' config/gateway.json
```

#### 2. 路径错误
```bash
# 确保配置文件路径正确
ls -la config/gateway.json

# 修改日志文件路径
sed -i 's|"file": "../logs/gateway.log"|"file": "./logs/gateway.log"|' config/gateway.json
```

#### 3. 权限问题
```bash
# 确保脚本有执行权限
chmod +x scripts/*.sh

# 确保日志目录可写
mkdir -p logs
chmod 755 logs
```

## 📝 配置备份

### 自动备份脚本
```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="config-backups"
mkdir -p $BACKUP_DIR
cp config/gateway.json $BACKUP_DIR/gateway-$(date +%Y%m%d-%H%M%S).json
echo "配置已备份到: $BACKUP_DIR/"
```

### 恢复配置
```bash
# 恢复最新备份
cp config-backups/gateway-*.json config/gateway.json
```

---

**配置说明完成**  
**最后更新**: 2026-03-21