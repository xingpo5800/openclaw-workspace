# LocalAI 模型配置修复指南

## 问题诊断
- ✅ LocalAI服务运行正常：http://192.168.8.171:8080
- ✅ 可用模型：Qwen3.5-2B-Q8_0_claude.gguf
- ❌ 配置错误：试图加载不存在的模型 qwen3.5-2B

## 解决方案

### 方法1：使用正确的模型名称
```bash
# 使用正确的模型名称进行对话
curl -X POST http://192.168.8.171:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.5-2B-Q8_0_claude.gguf",
    "messages": [
      {"role": "user", "content": "你好！"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### 方法2：检查并修复配置文件
找到LocalAI的配置文件（通常在以下位置）：
```bash
# 查找配置文件
find /path/to/localai -name "*.yaml" -o -name "*.yml" | grep -i localai

# 常见配置文件位置
# /etc/localai/config.yaml
# /opt/localai/config.yaml
# ~/.config/localai/config.yaml
```

修复配置文件中的模型名称：
```yaml
models:
  - name: Qwen3.5-2B-Q8_0_claude.gguf
    path: /path/to/models/Qwen3.5-2B-Q8_0_claude.gguf
    parameters:
      n_ctx: 2048
      n_threads: 2
      temperature: 0.7
```

### 方法3：重新配置模型
```bash
# 1. 停止LocalAI服务
sudo systemctl stop localai
# 或者
pkill -f localai

# 2. 检查模型文件位置
ls -la /path/to/models/

# 3. 重新配置
# 编辑配置文件，确保模型名称和路径正确

# 4. 重启LocalAI服务
sudo systemctl start localai
# 或者
/path/to/localai/localai
```

### 方法4：使用OpenAI兼容接口
```python
import requests

# 配置LocalAI客户端
localai_url = "http://192.168.8.171:8080"
api_key = "not-needed"  # LocalAI不需要API密钥

def chat_with_localai(message, model="Qwen3.5-2B-Q8_0_claude.gguf"):
    response = requests.post(
        f"{localai_url}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
    )
    return response.json()

# 使用示例
response = chat_with_localai("你好，LocalAI！")
print(response['choices'][0]['message']['content'])
```

### 方法5：检查模型文件完整性
```bash
# 检查模型文件是否存在
ls -la /path/to/models/Qwen3.5-2B-Q8_0_claude.gguf

# 检查文件大小（应该有几个GB）
du -h /path/to/models/Qwen3.5-2B-Q8_0_claude.gguf

# 检查文件权限
chmod 644 /path/to/models/Qwen3.5-2B-Q8_0_claude.gguf
```

## 验证修复
修复后，使用以下命令验证：
```bash
# 检查模型列表
curl http://192.168.8.171:8080/v1/models

# 测试对话
curl -X POST http://192.168.8.171:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.5-2B-Q8_0_claude.gguf",
    "messages": [{"role": "user", "content": "测试"}]
  }'
```

## 常见问题排查

### 问题1：模型文件不存在
**症状**：`gguf_init_from_file: failed to open GGUF file`
**解决**：
1. 确认模型文件已下载到正确位置
2. 检查文件路径和权限
3. 重新下载模型文件

### 问题2：模型名称不匹配
**症状**：模型列表中有模型，但配置中找不到
**解决**：
1. 使用模型列表中的完整名称
2. 更新配置文件中的模型名称

### 问题3：权限问题
**症状**：无法访问模型文件
**解决**：
1. 检查文件权限
2. 确保LocalAI有读取权限

## 总结
主要问题是配置文件中的模型名称不正确。使用正确的模型名称 `Qwen3.5-2B-Q8_0_claude.gguf` 即可解决问题。