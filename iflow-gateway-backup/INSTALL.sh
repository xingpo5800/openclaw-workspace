#!/bin/bash
# OpenClaw iFlow Gateway 一键安装脚本

echo "🚀 OpenClaw iFlow Gateway 安装程序"
echo "=================================="

# 检查 Python 版本
echo "🔍 检查系统环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 未安装，请先安装 Python 3.9+"
    exit 1
fi

# 检查 pip
echo "🔍 检查 pip..."
pip3 --version
if [ $? -ne 0 ]; then
    echo "❌ pip 未安装，请先安装 pip"
    exit 1
fi

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p logs
mkdir -p config/backups

# 备份现有配置
if [ -f "config/gateway.json" ]; then
    cp config/gateway.json config/backups/gateway.json.$(date +%Y%m%d_%H%M%S)
    echo "✅ 配置文件已备份"
fi

# 检查虚拟环境
if [ ! -d "iflow-sdk-venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv iflow-sdk-venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source iflow-sdk-venv/bin/activate

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装 Python 依赖包..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖包安装失败"
    exit 1
fi
echo "✅ 依赖包安装成功"

# 检查 iflow 命令
echo "🔍 检查 iFlow 命令..."
if command -v iflow &> /dev/null; then
    echo "✅ iFlow 命令可用"
else
    echo "⚠️  iFlow 命令未找到，请确保 iFlow 已安装"
    echo "   安装方法: npm install -g @iflow/cli"
fi

# 设置执行权限
echo "🔐 设置执行权限..."
chmod +x scripts/*.sh
chmod +x INSTALL.sh
echo "✅ 执行权限设置完成"

# 创建配置文件（如果不存在）
if [ ! -f "config/gateway.json" ]; then
    echo "📝 创建默认配置文件..."
    cat > config/gateway.json << 'EOF'
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
  },
  "logging": {
    "level": "INFO",
    "file": "../logs/gateway.log"
  }
}
EOF
    echo "✅ 配置文件创建完成"
fi

echo ""
echo "=================================="
echo "✅ 安装完成！"
echo ""
echo "📋 下一步操作："
echo "   1. 启动服务: ./scripts/start-all.sh"
echo "   2. 测试连接: ./scripts/test-connection.sh"
echo "   3. 查看日志: tail -f logs/server-simple.log"
echo ""
echo "📚 文档："
echo "   - README.md: 完整文档"
echo "   - QUICK_START.md: 快速开始"
echo "   - CONFIGURATION.md: 配置说明"
echo "   - API_REFERENCE.md: API 文档"
echo ""
echo "🛠️ 故障排除："
echo "   - 查看安装日志: cat install.log"
echo "   - 重新安装: ./INSTALL.sh"
echo "=================================="