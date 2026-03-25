#!/bin/bash
# OpenClaw iFlow 连接测试脚本

echo "🧪 测试 OpenClaw iFlow 连接"
echo "=================================="

# 测试 iFlow ACP
echo "🔍 测试 iFlow ACP 连接..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090 | grep -q "200\|404"; then
    echo "✅ iFlow ACP 服务正常"
else
    echo "❌ iFlow ACP 服务异常"
fi

# 测试智能网关
echo "🔍 测试智能网关连接..."
if curl -s http://127.0.0.1:8086/health | grep -q "healthy"; then
    echo "✅ 智能网关服务正常"
else
    echo "❌ 智能网关服务异常"
fi

# 测试聊天接口
echo "💬 测试聊天接口..."
response=$(curl -X POST http://127.0.0.1:8086/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "kimi-k2.5", "messages": [{"role": "user", "content": "测试连接"}]}' \
     --max-time 10 -s)

if echo "$response" | grep -q "choices"; then
    echo "✅ 聊天接口正常"
else
    echo "❌ 聊天接口异常"
fi

echo "=================================="
