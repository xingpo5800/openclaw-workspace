# OpenClaw iFlow Gateway 完整部署包

## 📁 项目结构

```
iflow-gateway-backup/
├── README.md                           # 项目说明文档
├── INSTALL.sh                          # 一键安装脚本
├── QUICK_START.md                      # 快速开始指南
├── CONFIGURATION.md                    # 配置说明
├── DEPLOYMENT.md                       # 部署指南
├── API_REFERENCE.md                    # API 接口文档
├── server.py                           # 完整版智能网关服务器
├── server-simple.py                    # 简化版网关服务器
├── config/
│   └── gateway.json                    # 网关配置文件
├── scripts/
│   ├── start-all.sh                    # 一键启动脚本
│   ├── stop-all.sh                     # 一键停止脚本
│   ├── test-connection.sh              # 连接测试脚本
│   └── install-iflow-sdk.sh            # iFlow SDK 安装脚本
├── iflow-sdk-venv/                     # iFlow SDK 虚拟环境
│   ├── bin/
│   ├── lib/
│   └── lib64/
├── logs/                              # 日志目录（自动创建）
├── core/                              # 核心代码目录
├── docs/                              # 文档目录
└── requirements.txt                    # Python 依赖包
```

## 🚀 快速开始

### 1. 一键安装
```bash
cd /Users/kevin/.openclaw/workspace/iflow-gateway-backup
./INSTALL.sh
```

### 2. 启动服务
```bash
./scripts/start-all.sh
```

### 3. 测试连接
```bash
./scripts/test-connection.sh
```

## 🎯 功能特性

### 核心功能
- ✅ **智能上下文管理** - 滑动窗口、自动摘要
- ✅ **响应缓存系统** - 提升重复请求响应速度
- ✅ **话题自动摘要** - 长对话智能压缩
- ✅ **智能分块处理** - 流式响应优化
- ✅ **性能监控统计** - 实时性能指标
- ✅ **错误恢复机制** - 自动重连和降级处理

### 技术架构
- 🔧 **Flask Web 服务器** - 提供 HTTP API 接口
- 🔧 **WebSocket 连接** - 与 iFlow ACP 通信
- 🔧 **异步处理** - 支持高并发请求
- 🔧 **配置管理** - 灵活的配置文件系统

## 🔧 配置说明

### 网关配置 (config/gateway.json)
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

### OpenClaw 配置
在 OpenClaw 配置文件中添加：
```json
"iflow": {
  "baseUrl": "http://127.0.0.1:8086/v1",
  "apiKey": "sk-7f2c30fe73e680c15527e4a6dfb5d55e",
  "api": "openai-completions",
  "models": [
    {
      "id": "kimi-k2.5",
      "name": "Kimi-K2.5 (iFlow SDK)",
      "reasoning": true,
      "contextWindow": 128000,
      "maxTokens": 32768
    }
    // 更多模型...
  ]
}
```

## 📡 API 接口

### 健康检查
```bash
GET http://127.0.0.1:8086/health
```

### 模型列表
```bash
GET http://127.0.0.1:8086/v1/models
```

### 聊天接口
```bash
POST http://127.0.0.1:8086/v1/chat/completions
Content-Type: application/json

{
  "model": "kimi-k2.5",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "stream": false,
  "topic_id": "optional-topic-id",
  "user_id": "optional-user-id"
}
```

### 流式聊天
```bash
POST http://127.0.0.1:8086/v1/chat/completions
Content-Type: application/json

{
  "model": "kimi-k2.5",
  "messages": [
    {"role": "user", "content": "请详细介绍一下人工智能"}
  ],
  "stream": true
}
```

## 🛠️ 管理命令

### 服务管理
```bash
# 启动所有服务
./scripts/start-all.sh

# 停止所有服务
./scripts stop-all.sh

# 测试连接
./scripts/test-connection.sh

# 安装依赖
./scripts/install-iflow-sdk.sh
```

### 手动管理
```bash
# 启动 iFlow ACP
nohup iflow --experimental-acp --stream --port 8090 > logs/iflow-acp.log 2>&1 &

# 启动网关服务器
nohup python3 server-simple.py > logs/server-simple.log 2>&1 &

# 查看服务状态
ps aux | grep -E "(iflow|server)" | grep -v grep

# 查看日志
tail -f logs/iflow-acp.log
tail -f logs/server-simple.log
```

## 📊 监控和日志

### 日志文件
- `logs/iflow-acp.log` - iFlow ACP 服务器日志
- `logs/server-simple.log` - 网关服务器日志
- `logs/gateway.log` - 完整版网关日志

### 监控指标
- 服务健康状态
- 缓存命中率
- 平均响应时间
- 错误率统计
- Token 使用量

## 🔍 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
lsof -i :8086
lsof -i :8090

# 查看错误日志
tail -f logs/iflow-acp.log
tail -f logs/server-simple.log
```

#### 2. iFlow SDK 安装失败
```bash
# 重新安装虚拟环境
rm -rf iflow-sdk-venv
./scripts/install-iflow-sdk.sh
```

#### 3. 连接测试失败
```bash
# 手动测试 iFlow ACP
curl -I http://127.0.0.1:8090/

# 测试网关健康检查
curl http://127.0.0.1:8086/health
```

### 性能优化
- 调整 `max_topics` 和 `max_tokens_per_topic`
- 优化 `chunk_size` 提升流式响应
- 启用压缩减少网络传输

## 📚 可用模型

### iFlow 模型列表
- **Kimi-K2.5** - 月之暗面最新模型
- **GLM-4.7** - 智谱 AI 高性能模型
- **GLM-5** - 智谱 AI 最新模型
- **Qwen3-Coder-Plus** - 通义千问编程模型
- **DeepSeek-V3.2** - DeepSeek 最新模型
- **MiniMax-M2.5** - MiniMax 新模型
- **Kimi-K2-Thinking** - 思考版 Kimi 模型

### 模型特性
- ✅ 支持 Reasoning 模式
- ✅ 大上下文窗口 (128K-204K)
- ✅ 高质量中文理解
- ✅ 专业领域知识

## 🔄 更新和维护

### 升级 iFlow SDK
```bash
# 进入项目目录
cd /Users/kevin/.openclaw/workspace/iflow-gateway-backup

# 重新安装依赖
source iflow-sdk-venv/bin/activate
pip install -r requirements.txt
```

### 备份配置
```bash
# 备份整个项目
tar -czf iflow-gateway-backup-$(date +%Y%m%d).tar.gz iflow-gateway-backup/

# 备份配置文件
cp config/gateway.json config/gateway.json.backup
```

## 📞 技术支持

### 联系信息
- 项目路径: `/Users/kevin/.openclaw/workspace/iflow-gateway-backup`
- 日志目录: `logs/`
- 配置文件: `config/gateway.json`

### 调试技巧
1. 查看 `logs/` 目录下的日志文件
2. 使用 `curl` 测试 API 接口
3. 检查端口占用情况
4. 验证 iFlow SDK 安装状态

---

## 📝 版本信息

- **版本**: v1.0.0
- **创建日期**: 2026-03-21
- **兼容性**: OpenClaw 2026.3.13+
- **Python**: 3.9+
- **操作系统**: macOS/Linux

## 📄 许可证

本项目基于 MIT 许可证开源。

---

**最后更新**: 2026-03-21 03:06