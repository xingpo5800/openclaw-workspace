# macOS 12.7.6 LocalAI 手动编译指南

## 系统要求
- macOS 12.7.6 Monterey
- Intel i5-4590t CPU
- 至少4GB内存
- Xcode命令行工具

## 编译步骤

### 1. 安装依赖
```bash
# 安装Xcode命令行工具
xcode-select --install

# 安装Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装编译依赖
brew install protobuf grpc-tools make cmake libomp llvm
```

### 2. 获取源码
```bash
# 克隆LocalAI仓库
git clone https://github.com/mudler/LocalAI.git
cd LocalAI

# 切换到兼容的Go版本
git checkout go1.21
```

### 3. 修改Go版本
```bash
# 编辑go.mod文件，将Go版本改为1.21
sed -i '' 's/go 1.26.0/go 1.21/' go.mod
```

### 4. 编译LocalAI
```bash
# 设置编译环境
export CGO_ENABLED=0
export GOOS=darwin
export GOARCH=amd64
export GOAMD64=v1

# 编译
make protogen-go
make build-localai
```

### 5. 测试编译结果
```bash
# 测试可执行文件
./localai --version

# 查看文件信息
file localai
```

### 6. 安装
```bash
# 安装到系统
chmod +x localai
sudo cp localai /usr/local/bin/

# 测试安装
localai --help
```

## 注意事项

1. **Go版本兼容性**：
   - 使用Go 1.21而不是最新版本
   - 确保与macOS 12.7.6兼容

2. **编译优化**：
   - 禁用CGO以减少依赖
   - 使用amd64架构确保Intel兼容

3. **依赖管理**：
   - 确保所有依赖都正确安装
   - 如果遇到问题，可以尝试更新Homebrew

## 故障排除

### 如果编译失败：
```bash
# 检查Go版本
go version

# 重新安装依赖
brew reinstall protobuf grpc-tools make cmake libomp llvm

# 清理编译缓存
make clean
```

### 如果运行失败：
```bash
# 检查系统兼容性
uname -a
sw_vers

# 检查文件权限
ls -la localai
```

## 下载模型
```bash
# 下载适合的模型
localai-llama download llama3:2b
localai-llama download qwen:2b
```

## 启动服务
```bash
# 启动LocalAI服务
localai

# 后台运行
nohup localai > localai.log 2>&1 &

# 查看日志
tail -f localai.log
```