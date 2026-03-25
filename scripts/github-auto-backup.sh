#!/bin/bash
# OpenClaw GitHub自动备份脚本

# 配置
BACKUP_BASE_DIR="/Volumes/data-backup/openclawbackup"
BACKUP_DIR="$BACKUP_BASE_DIR/backup-$(date +%Y-%m-%d)"
GITHUB_REPO="kevin/openclaw-backup"  # 使用毅哥的GitHub仓库
GITHUB_TOKEN="$GH_TOKEN"  # 使用环境变量中的token
LOG_FILE="/Users/kevin/.openclaw/workspace/logs/github-backup-$(date +%Y-%m-%d).log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "==================================" | tee -a "$LOG_FILE"
echo "🚀 开始GitHub自动备份: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 备份目录不存在: $BACKUP_DIR" | tee -a "$LOG_FILE"
    echo "请先运行本地备份脚本" | tee -a "$LOG_FILE"
    exit 1
fi

# 进入备份目录
cd "$BACKUP_DIR"
echo "📁 进入备份目录: $BACKUP_DIR" | tee -a "$LOG_FILE"

# 检查是否已经是Git仓库
if [ ! -d ".git" ]; then
    echo "🔧 初始化Git仓库..." | tee -a "$LOG_FILE"
    git init
    echo "✅ Git仓库初始化完成" | tee -a "$LOG_FILE"
fi

# 配置Git
echo "⚙️  配置Git..." | tee -a "$LOG_FILE"
git config user.name "OpenClaw Auto Backup"
git config user.email "openclaw@backup.local"

# 添加远程仓库
if ! git remote -v | grep -q "origin"; then
    echo "🔗 添加远程仓库..." | tee -a "$LOG_FILE"
    git remote add origin "https://$GITHUB_TOKEN@github.com/$GITHUB_REPO.git"
    echo "✅ 远程仓库添加完成" | tee -a "$LOG_FILE"
fi

# 添加文件到Git
echo "📤 添加文件到Git..." | tee -a "$LOG_FILE"
git add .

# 检查是否有变更
if git diff --cached --quiet; then
    echo "ℹ️  没有新的变更需要提交" | tee -a "$LOG_FILE"
else
    # 提交变更
    echo "💾 提交变更..." | tee -a "$LOG_FILE"
    git commit -m "自动备份 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ 变更提交完成" | tee -a "$LOG_FILE"
    
    # 推送到GitHub
    echo "🚀 推送到GitHub..." | tee -a "$LOG_FILE"
    if git push -u origin main; then
        echo "✅ 成功推送到GitHub!" | tee -a "$LOG_FILE"
    else
        echo "❌ 推送到GitHub失败!" | tee -a "$LOG_FILE"
        echo "请检查GitHub token和仓库权限" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

# 记录结束时间
echo "" | tee -a "$LOG_FILE"
echo "✅ GitHub自动备份完成!" | tee -a "$LOG_FILE"
echo "📊 备份信息:" | tee -a "$LOG_FILE"
echo "   备份目录: $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "   GitHub仓库: $GITHUB_REPO" | tee -a "$LOG_FILE"
echo "   备份时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 显示结果
echo ""
echo "🚀 GitHub自动备份完成!"
echo "   备份目录: $BACKUP_DIR"
echo "   GitHub仓库: $GITHUB_REPO"
echo "   日志文件: $LOG_FILE"
echo ""