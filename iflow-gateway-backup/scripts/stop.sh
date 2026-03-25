#!/bin/bash
# OpenClaw iFlow 智能网关停止脚本

echo "🛑 停止 OpenClaw iFlow 智能网关"
echo "=================================="

# 查找并停止进程
PIDS=$(ps aux | grep "python3.*server.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ 没有找到运行中的网关进程"
else
    echo "🔍 找到进程: $PIDS"
    echo "⏹️  停止进程..."
    kill -9 $PIDS 2>/dev/null
    echo "✅ 网关已停止"
fi

echo "=================================="