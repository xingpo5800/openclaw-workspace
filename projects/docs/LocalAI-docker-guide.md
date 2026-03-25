# macOS 12.7.6 LocalAI Docker 方案

## 为什么选择Docker
- 绕过系统版本限制
- 自动解决依赖问题
- 环境隔离，避免冲突
- 便于管理和迁移

## 安装Docker Desktop

### 1. 下载Docker Desktop
```bash
# 访问官方下载页面
# https://www.docker.com/products/docker-desktop/
```

### 2. 安装Docker Desktop
```bash
# 拖拽DMG文件到Applications
# 启动Docker Desktop
# 按照设置向导完成安装
```

### 3. 验证安装
```bash
# 检查Docker版本
docker --version

# 测试Docker运行
docker run hello-world
```

## 使用Docker运行LocalAI

### 1. 拉取LocalAI镜像
```bash
# 拉取最新版本
docker pull localai/localai:latest

# 拉取特定版本（可选）
docker pull localai/localai:v2.0.0
```

### 2. 运行LocalAI容器
```bash
# 基本运行
docker run -d -p 8080:8080 localai/localai:latest

# 高级配置运行
docker run -d \
  -p 8080:8080 \
  -v /Users/yourusername/models:/models \
  -v /Users/yourusername/config:/config \
  --name localai \
  localai/localai:latest
```

### 3. 测试LocalAI服务
```bash
# 检查容器状态
docker ps

# 测试API
curl http://localhost:8080/v1/models

# 查看日志
docker logs localai
```

## 下载模型到容器

### 1. 进入容器
```bash
# 进入容器命令行
docker exec -it localai /bin/bash
```

### 2. 下载模型
```bash
# 在容器内下载模型
llama-cli --hf-repo TheBloke/Llama-2-7B-GGUF --hf-file llama-2-7b.Q4_K_M.gguf

# 或者使用内置下载工具
localai-llama download llama3:2b
```

### 3. 退出容器
```bash
# 退出容器
exit
```

## 本地文件挂载

### 1. 创建模型目录
```bash
# 创建本地模型目录
mkdir -p ~/models ~/config
```

### 2. 下载模型到本地
```bash
# 使用Git LFS下载模型
cd ~/models
git lfs install
git clone https://huggingface.co/TheBloke/Llama-2-7B-GGUF
```

### 3. 挂载本地目录运行
```bash
# 挂载本地目录运行
docker run -d \
  -p 8080:8080 \
  -v ~/models:/models \
  -v ~/config:/config \
  --name localai \
  localai/localai:latest
```

## 配置文件

### 1. 创建配置文件
```bash
# 创建配置目录
mkdir -p ~/config

# 创建配置文件
cat > ~/config/config.yaml << 'EOF'
models:
  - name: llama3:2b
    path: /models/llama-2-7b.Q4_K_M.gguf
    parameters:
      n_ctx: 2048
      n_threads: 2
      temperature: 0.7

backend: llama-cpp

api:
  address: :8080
EOF
```

### 2. 使用配置文件运行
```bash
# 挂载配置文件运行
docker run -d \
  -p 8080:8080 \
  -v ~/models:/models \
  -v ~/config:/config \
  --name localai \
  localai/localai:latest
```

## 使用LocalAI API

### 1. 基本API调用
```bash
# 查看可用模型
curl http://localhost:8080/v1/models

# 进行对话
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:2b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 2. Python客户端示例
```python
import openai

# 配置客户端
client = openai.OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

# 进行对话
response = client.chat.completions.create(
    model="llama3:2b",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### 3. JavaScript客户端示例
```javascript
const { OpenAI } = require('openai');

const client = new OpenAI({
  baseURL: 'http://localhost:8080/v1',
  apiKey: 'not-needed'
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'llama3:2b',
    messages: [
      { role: 'user', content: 'Hello!' }
    ]
  });
  
  console.log(response.choices[0].message.content);
}

chat();
```

## 管理容器

### 1. 查看容器状态
```bash
# 查看所有容器
docker ps -a

# 查看容器日志
docker logs localai

# 停止容器
docker stop localai

# 启动容器
docker start localai

# 删除容器
docker rm localai
```

### 2. 备份和恢复
```bash
# 备份模型目录
tar -czf models-backup.tar.gz ~/models

# 恢复模型目录
tar -xzf models-backup.tar.gz
```

## 性能优化

### 1. 资源限制
```bash
# 限制内存使用
docker run -d \
  -p 8080:8080 \
  --memory="4g" \
  --memory-swap="4g" \
  localai/localai:latest
```

### 2. CPU优化
```bash
# 限制CPU使用
docker run -d \
  -p 8080:8080 \
  --cpus="2.0" \
  localai/localai:latest
```

## 故障排除

### 1. 常见问题
```bash
# 检查Docker状态
docker info

# 检查容器资源使用
docker stats localai

# 清理Docker资源
docker system prune
```

### 2. 网络问题
```bash
# 检查端口占用
lsof -i :8080

# 测试网络连接
curl http://localhost:8080/health
```

## 总结

Docker方案的优势：
- ✅ 绕过系统版本限制
- ✅ 自动解决依赖问题
- ✅ 便于管理和迁移
- ✅ 环境隔离，避免冲突
- ✅ 支持模型本地存储
- ✅ 便于API集成

这是最适合您macOS 12.7.6系统的方案！