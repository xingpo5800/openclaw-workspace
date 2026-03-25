#!/bin/bash
# OpenClaw iFlow 智能网关启动脚本

echo "🚀 启动 OpenClaw iFlow 智能网关"
echo "=================================="

# 激活虚拟环境
source ../iflow-sdk-venv/bin/activate

# 检查 Flask
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask 未安装，正在安装..."
    pip install flask flask-cors
fi

# 创建日志目录
mkdir -p ../logs

# 启动服务器
echo "📋 启动智能网关服务器..."
echo "📡 HTTP 端口: 8086"
echo "🔌 iFlow ACP 端口: 8090"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=================================="

python3 ../server.py
