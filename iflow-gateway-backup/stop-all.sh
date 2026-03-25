#!/bin/bash
# OpenClaw iFlow 一键停止脚本

echo "🛑 停止 OpenClaw iFlow 服务"
echo "=================================="

# 停止 iFlow ACP
echo "🔌 停止 iFlow ACP 服务器..."
pkill -f "iflow.*experimental-acp"

# 停止智能网关
echo "📡 停止智能网关服务器..."
pkill -f "python3.*server.py"

# 等待进程停止
sleep 2

# 检查进程
if pgrep -f "iflow.*experimental-acp" > /dev/null; then
    echo "⚠️  iFlow ACP 强制停止..."
    pkill -9 -f "iflow.*experimental-acp"
fi

if pgrep -f "python3.*server.py" > /dev/null; then
    echo "⚠️  智能网关强制停止..."
    pkill -9 -f "python3.*server.py"
fi

echo "✅ 所有服务已停止"
echo "=================================="
