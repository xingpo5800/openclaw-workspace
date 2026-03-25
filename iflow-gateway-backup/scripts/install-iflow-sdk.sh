#!/bin/bash
# iFlow SDK 安装脚本

echo "🔧 安装 iFlow SDK"
echo "=================================="

# 激活虚拟环境
source iflow-sdk-venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 iFlow SDK
echo "📦 安装 iFlow SDK..."
pip install iflow-sdk

# 安装其他依赖
echo "📦 安装其他依赖..."
pip install flask flask-cors websockets aiohttp pydantic

# 验证安装
echo "🔍 验证安装..."
python -c "from iflow_sdk import query_sync; print('✅ iFlow SDK 安装成功')"
if [ $? -eq 0 ]; then
    echo "✅ iFlow SDK 安装成功"
else
    echo "❌ iFlow SDK 安装失败"
    exit 1
fi

echo "=================================="
echo "✅ iFlow SDK 安装完成！"
echo ""