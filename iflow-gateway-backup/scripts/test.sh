#!/bin/bash
# OpenClaw iFlow 智能网关测试脚本

echo "🧪 测试 OpenClaw iFlow 智能网关"
echo "=================================="

# 检查服务器是否运行
echo "🔍 检查服务器状态..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8086/health | grep -q "200"; then
    echo "✅ 服务器正在运行 (端口 8086)"
    
    # 测试健康检查
    echo "🏥 测试健康检查接口..."
    curl -s http://127.0.0.1:8086/health | head -3
    
    # 测试模型列表
    echo ""
    echo "📋 测试模型列表接口..."
    curl -s http://127.0.0.1:8086/v1/models | head -3
    
    # 测试聊天接口
    echo ""
    echo "💬 测试聊天接口..."
    curl -X POST http://127.0.0.1:8086/v1/chat/completions \
         -H "Content-Type: application/json" \
         -d '{"model": "kimi-k2.5", "messages": [{"role": "user", "content": "你好，请回复测试成功"}]}' \
         --max-time 10 | head -2
    
    echo ""
    echo "✅ 所有测试完成"
else
    echo "❌ 服务器未运行，请先启动: ./scripts/start.sh"
    exit 1
fi

echo "=================================="