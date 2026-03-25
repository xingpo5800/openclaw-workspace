#!/bin/bash
# OpenClaw 完全自动备份脚本 (本地 + GitHub)

# 配置
LOG_FILE="/Users/kevin/.openclaw/workspace/logs/full-backup-$(date +%Y-%m-%d).log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "==================================" | tee -a "$LOG_FILE"
echo "🔄 开始完整自动备份: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 第一步：本地备份
echo "📦 第一步：执行本地备份..." | tee -a "$LOG_FILE"
if /Users/kevin/.openclaw/workspace/scripts/auto-backup.sh >> "$LOG_FILE" 2>&1; then
    echo "✅ 本地备份完成" | tee -a "$LOG_FILE"
else
    echo "❌ 本地备份失败" | tee -a "$LOG_FILE"
    exit 1
fi

# 第二步：GitHub备份
echo "" | tee -a "$LOG_FILE"
echo "🚀 第二步：执行GitHub备份..." | tee -a "$LOG_FILE"
if /Users/kevin/.openclaw/workspace/scripts/github-auto-backup.sh >> "$LOG_FILE" 2>&1; then
    echo "✅ GitHub备份完成" | tee -a "$LOG_FILE"
else
    echo "❌ GitHub备份失败" | tee -a "$LOG_FILE"
    exit 1
fi

# 记录结束时间
echo "" | tee -a "$LOG_FILE"
echo "🎉 完整自动备份完成!" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 显示结果
echo ""
echo "🎉 完整自动备份完成!"
echo "   本地备份: /Volumes/data-backup/openclawbackup/"
echo "   GitHub备份: 已推送到远程仓库"
echo "   日志文件: $LOG_FILE"
echo ""