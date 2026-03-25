#!/bin/bash
# OpenClaw iFlow 一键启动脚本

echo "🚀 OpenClaw iFlow 一键启动"
echo "=================================="

# 激活虚拟环境
source ../iflow-sdk-venv/bin/activate

# 启动 iFlow ACP
echo "🔌 启动 iFlow ACP 服务器..."
nohup iflow --experimental-acp --stream --port 8090 > ../logs/iflow-acp.log 2>&1 &
sleep 3

# 启动智能网关
echo "📡 启动智能网关服务器..."
nohup python3 ../server.py > ../logs/gateway.log 2>&1 &
sleep 3

# 测试连接
echo "🧪 测试服务连接..."
../scripts/test-connection.sh

echo "=================================="
echo "✅ 所有服务已启动"
echo "📋 查看日志:"
echo "   - iFlow ACP: tail -f ../logs/iflow-acp.log"
echo "   - 智能网关: tail -f ../logs/gateway.log"
echo "🛑 停止服务: ./stop-all.sh"
echo "=================================="
