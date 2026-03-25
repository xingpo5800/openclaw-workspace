# OpenClaw 高效集成 iFlow-CLI 大模型完整部署指南

## 📋 文档概述

本文档详细介绍如何在 OpenClaw 中高效集成 iFlow-CLI 大模型，包括完整的安装、配置、部署和测试流程。

## 🎯 系统要求

### 硬件要求
- **CPU**: x86_64 架构，2核以上
- **内存**: 4GB 以上，推荐 8GB
- **存储**: 1GB 可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: macOS 10.14+, Windows 10+, Ubuntu 18.04+
- **Python**: 3.8+ (推荐 3.9)
- **Node.js**: 16+ (OpenClaw 要求)
- **Git**: 最新版本

## 📦 完整依赖清单

### 1. 系统级依赖

#### macOS
```bash
# 安装 Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装必需工具
brew install python@3.9 git nodejs npm
```

#### Ubuntu/Debian
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必需工具
sudo apt install -y python3.9 python3.9-venv git nodejs npm
```

#### Windows
```powershell
# 安装 Chocolatey (如果没有)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装必需工具
choco install python3 git nodejs npm
```

### 2. Python 虚拟环境设置

#### 创建虚拟环境
```bash
# 进入项目目录
cd /Users/kevin/.openclaw

# 创建 Python 3.9 虚拟环境
python3.9 -m venv iflow-sdk-venv

# 激活虚拟环境
# macOS/Linux:
source iflow-sdk-venv/bin/activate
# Windows:
iflow-sdk-venv\Scripts\activate
```

#### 升级 pip
```bash
pip install --upgrade pip
```

### 3. 安装 iFlow SDK

#### 方法一：pip 安装（推荐）
```bash
# 安装 iFlow CLI
pip install iflow-cli

# 验证安装
iflow --version
```

#### 方法二：源码安装
```bash
# 克隆 iFlow CLI 仓库
git clone https://github.com/iflow-ai/iflow-cli.git
cd iflow-cli

# 安装开发版本
pip install -e .
```

#### 方法三：使用我们提供的安装脚本
```bash
cd /Users/kevin/.openclaw/iflow-gateway
./scripts/install-iflow-sdk.sh
```

### 4. 安装 OpenClaw 依赖

#### 安装 OpenClaw
```bash
# 如果尚未安装 OpenClaw
npm install -g openclaw

# 或者从源码安装
git clone https://github.com/openclaw/openclaw.git
cd openclaw
npm install
npm link
```

#### 安装 Python 依赖
```bash
# 进入网关目录
cd /Users/kevin/.openclaw/iflow-gateway

# 安装依赖
pip install -r requirements.txt

# 或者手动安装
pip install flask flask-cors iflow-sdk
```

### 5. 安装系统工具

#### 安装 ripgrep (文本搜索)
```bash
# macOS
brew install ripgrep

# Ubuntu
sudo apt install ripgrep

# Windows
choco install ripgrep
```

#### 安装 gf (Git Flow 工具)
```bash
# macOS
brew install git-flow-avh

# Ubuntu
sudo apt install git-flow

# Windows
choco install git-flow
```

#### 安装 ffmpeg (多媒体处理)
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

## 🔧 配置设置

### 1. 配置 iFlow CLI

#### 初始化 iFlow CLI
```bash
iflow init
```

#### 配置 API 密钥
```bash
iflow config set api-key YOUR_API_KEY
```

#### 测试连接
```bash
iflow test-connection
```

### 2. 配置 OpenClaw

#### 修改 OpenClaw 配置
编辑 `/Users/kevin/.openclaw/openclaw.json`：

```json
{
  "providers": {
    "iflow": {
      "baseUrl": "http://127.0.0.1:8086/v1",
      "api": "openai-completions",
      "models": [
        {
          "id": "kimi-k2.5",
          "name": "灵犀",
          "alias": "灵犀"
        },
        {
          "id": "glm-5",
          "name": "灵犀",
          "alias": "灵犀"
        }
      ]
    }
  }
}
```

### 3. 配置智能网关

#### 编辑网关配置
编辑 `/Users/kevin/.openclaw/iflow-gateway/config/gateway.json`：

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
  }
}
```

## 🚀 启动服务

### 1. 启动 iFlow ACP 服务器

#### 使用启动脚本
```bash
cd /Users/kevin/.openclaw
./start-iflow-sdk-local.sh
```

#### 手动启动
```bash
# 激活虚拟环境
source iflow-sdk-venv/bin/activate

# 启动 iFlow ACP 服务器
iflow --experimental-acp --stream --port 8090
```

### 2. 启动智能网关

#### 使用启动脚本
```bash
cd /Users/kevin/.openclaw/iflow-gateway
./scripts/start.sh
```

#### 手动启动
```bash
# 激活虚拟环境
source /Users/kevin/.openclaw/iflow-sdk-venv/bin/activate

# 启动网关服务器
python3 /Users/kevin/.openclaw/server.py
```

### 3. 验证服务状态

#### 检查 iFlow ACP
```bash
curl -s http://127.0.0.1:8090 | head -3
```

#### 检查智能网关
```bash
curl -s http://127.0.0.1:8086/health
```

#### 运行测试脚本
```bash
cd /Users/kevin/.openclaw/iflow-gateway
./scripts/test.sh
```

## 🧪 测试验证

### 1. 基础功能测试

#### 健康检查
```bash
curl -s http://127.0.0.1:8086/health
```

#### 模型列表
```bash
curl -s http://127.0.0.1:8086/v1/models
```

#### 聊天测试
```bash
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "kimi-k2.5", "messages": [{"role": "user", "content": "你好，请回复测试成功"}]}' \
     --max-time 10
```

### 2. 高级功能测试

#### 长文本测试
```bash
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "kimi-k2.5", 
       "messages": [{"role": "user", "content": "请详细介绍一下人工智能的发展历史，包括机器学习、深度学习、自然语言处理等主要技术领域的突破和挑战。"}]
     }' \
     --max-time 30
```

#### 流式响应测试
```bash
curl -X POST http://127.0.0.1:8086/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "kimi-k2.5", 
       "messages": [{"role": "user", "content": "你好"}],
       "stream": true
     }'
```

### 3. 性能测试

#### 并发请求测试
```bash
# 使用 ab 进行压力测试
ab -n 100 -c 10 -p test.json -T application/json http://127.0.0.1:8086/v1/chat/completions
```

## 🔍 故障排除

### 常见问题

#### 1. Flask 模块未找到
```bash
# 解决方案：安装 Flask
pip install flask flask-cors
```

#### 2. iFlow SDK 未找到
```bash
# 解决方案：安装 iFlow CLI
pip install iflow-cli
```

#### 3. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8086
lsof -i :8090

# 停止占用进程
kill -9 <PID>
```

#### 4. 虚拟环境未激活
```bash
# 激活虚拟环境
source /Users/kevin/.openclaw/iflow-sdk-venv/bin/activate
```

#### 5. 权限问题
```bash
# 给脚本执行权限
chmod +x /Users/kevin/.openclaw/iflow-gateway/scripts/*.sh
```

### 日志查看

#### 查看网关日志
```bash
tail -f /Users/kevin/.openclaw/logs/iflow-sdk-standalone.log
```

#### 查看 iFlow 日志
```bash
tail -f /Users/kevin/.openclaw/logs/iflow-acp.log
```

#### 查看 OpenClaw 日志
```bash
tail -f /tmp/openclaw/openclaw-*.log
```

## 📋 部署检查清单

- [ ] 系统要求检查
- [ ] Python 3.9+ 安装
- [ ] 虚拟环境创建
- [ ] iFlow CLI 安装
- [ ] 系统工具安装 (ripgrep, gf, ffmpeg)
- [ ] Python 依赖安装
- [ ] iFlow CLI 配置
- [ ] OpenClaw 配置修改
- [ ] 智能网关配置
- [ ] iFlow ACP 服务器启动
- [ ] 智能网关服务器启动
- [ ] 基础功能测试
- [ ] 高级功能测试
- [ ] 性能测试
- [ ] 故障排除准备

## 🎯 下一步

完成部署后，您可以：

1. **切换到 iFlow 模型**进行测试
2. **体验智能网关功能**：上下文管理、响应缓存、话题摘要等
3. **进行性能优化**根据实际使用情况调整配置
4. **部署到生产环境**按照生产环境要求进行配置

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看相关日志文件
3. 确认所有依赖都已正确安装
4. 验证网络连接和端口配置

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**适用版本**: OpenClaw 最新版本, iFlow CLI 0.5+