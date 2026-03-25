# OpenClaw iFlow Gateway 快速开始指南

## 🚀 5分钟快速部署

### 第一步：进入项目目录
```bash
cd /Users/kevin/.openclaw/workspace/iflow-gateway-backup
```

### 第二步：一键安装
```bash
./INSTALL.sh
```

### 第三步：启动服务
```bash
./scripts/start-all.sh
```

### 第四步：测试连接
```bash
./scripts/test-connection.sh
```

## 🎯 验证安装

### 检查服务状态
```bash
# 应该看到两个进程在运行
ps aux | grep -E "(iflow|server)" | grep -v grep
```

### 测试 API 接口
```bash
# 健康检查
curl http://127.0.0.1:8086/health

# 获取模型列表
curl http://127.0.0.1:8086/v1/models

# 测试聊天
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "kimi-k2.5", "messages": [{"role": "user", "content": "你好"}]}'
```

## 🔧 OpenClaw 配置

在 OpenClaw 配置文件中确保有以下配置：

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
  ]
}
```

## 📋 可用模型

- **kimi-k2.5** - 月之暗面最新模型
- **glm-4.7** - 智谱 AI 高性能模型
- **glm-5** - 智谱 AI 最新模型
- **qwen3-coder-plus** - 通义千问编程模型
- **deepseek-v3.2** - DeepSeek 最新模型
- **minimax-m2.5** - MiniMax 新模型
- **kimi-k2-thinking** - 思考版 Kimi 模型

## 🛠️ 常用命令

### 服务管理
```bash
# 启动服务
./scripts/start-all.sh

# 停止服务
./scripts/stop-all.sh

# 测试连接
./scripts/test-connection.sh
```

### 日志查看
```bash
# 查看 iFlow 日志
tail -f logs/iflow-acp.log

# 查看网关日志
tail -f logs/server-simple.log
```

## 🔍 故障排除

### 如果启动失败
1. 检查端口是否被占用：
   ```bash
   lsof -i :8086
   lsof -i :8090
   ```

2. 重新安装依赖：
   ```bash
   ./scripts/install-iflow-sdk.sh
   ```

3. 查看详细日志：
   ```bash
   cat logs/iflow-acp.log
   cat logs/server-simple.log
   ```

### 如果连接测试失败
1. 确保 iFlow ACP 先启动：
   ```bash
   ps aux | grep iflow | grep -v grep
   ```

2. 测试基本连接：
   ```bash
   curl http://127.0.0.1:8086/health
   ```

## 🎉 完成！

现在你已经成功部署了 OpenClaw iFlow Gateway，可以开始使用 iFlow 的各种模型了！

**服务地址**:
- HTTP API: `http://127.0.0.1:8086`
- iFlow ACP: `ws://127.0.0.1:8090/acp`

---

**快速开始完成时间**: 约 5 分钟  
**最后更新**: 2026-03-21