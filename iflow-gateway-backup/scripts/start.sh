#!/bin/bash
# OpenClaw iFlow 智能网关启动脚本

echo "🚀 启动 OpenClaw iFlow 智能网关"
echo "=================================="

# 检查虚拟环境
VENV_DIR="../../iflow-sdk-venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 虚拟环境未找到: $VENV_DIR"
    echo "请先运行: ../scripts/install-iflow-sdk.sh"
    exit 1
fi

# 激活虚拟环境
echo "🐍 激活虚拟环境..."
source $VENV_DIR/bin/activate

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

python3 ../../server-simple.py
