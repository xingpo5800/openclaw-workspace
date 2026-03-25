#!/bin/bash
# OpenClaw 数据自动备份脚本

# 配置
BACKUP_BASE_DIR="/Volumes/data-backup/openclawbackup"
BACKUP_DIR="$BACKUP_BASE_DIR/backup-$(date +%Y-%m-%d)"
SOURCE_DIR="/Users/kevin/.openclaw/workspace"
LOG_FILE="/Users/kevin/.openclaw/workspace/logs/backup-$(date +%Y-%m-%d).log"
GITHUB_REPO="your-username/openclaw-backup"  # 请替换为你的GitHub仓库

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "==================================" | tee -a "$LOG_FILE"
echo "🔄 开始备份: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 检查备份基础目录
if [ ! -d "/Volumes/data-backup" ]; then
    echo "❌ 备份目录不存在: /Volumes/data-backup" | tee -a "$LOG_FILE"
    mkdir -p "/Volumes/data-backup"
    echo "✅ 已创建备份目录" | tee -a "$LOG_FILE"
fi

# 创建基础备份目录
echo "📁 创建基础备份目录: $BACKUP_BASE_DIR" | tee -a "$LOG_FILE"
mkdir -p "$BACKUP_BASE_DIR"

# 创建备份目录
echo "📁 创建备份目录: $BACKUP_DIR" | tee -a "$LOG_FILE"
mkdir -p "$BACKUP_DIR"

# 备份重要文件和目录
echo "📋 开始备份文件..." | tee -a "$LOG_FILE"

# 备份配置文件
echo "  📄 备份配置文件..." | tee -a "$LOG_FILE"
cp -r "/Users/kevin/.openclaw/openclaw.json" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ openclaw.json" | tee -a "$LOG_FILE" || echo "    ❌ openclaw.json 失败" | tee -a "$LOG_FILE"

# 备份记忆文件
echo "  🧠 备份记忆文件..." | tee -a "$LOG_FILE"
cp -r "/Users/kevin/.openclaw/workspace/memory" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ memory/" | tee -a "$LOG_FILE" || echo "    ❌ memory/ 失败" | tee -a "$LOG_FILE"

# 备份规则文件
echo "  📜 备份规则文件..." | tee -a "$LOG_FILE"
cp -r "/Users/kevin/.openclaw/workspace/rules" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ rules/" | tee -a "$LOG_FILE" || echo "    ❌ rules/ 失败" | tee -a "$LOG_FILE"

# 备份任务管理
echo "  📋 备份任务管理..." | tee -a "$LOG_FILE"
cp -r "/Users/kevin/.openclaw/workspace/tasks" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ tasks/" | tee -a "$LOG_FILE" || echo "    ❌ tasks/ 失败" | tee -a "$LOG_FILE"

# 备份重要脚本
echo "  🛠️ 备份脚本文件..." | tee -a "$LOG_FILE"
cp -r "/Users/kevin/.openclaw/workspace/scripts" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ scripts/" | tee -a "$LOG_FILE" || echo "    ❌ scripts/ 失败" | tee -a "$LOG_FILE"

# 备份日志文件（最近7天）
echo "  📊 备份日志文件..." | tee -a "$LOG_FILE"
find "/Users/kevin/.openclaw/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null && echo "    ✅ logs/ (最近7天)" | tee -a "$LOG_FILE" || echo "    ❌ logs/ 失败" | tee -a "$LOG_FILE"

# 创建备份信息文件
cat > "$BACKUP_DIR/backup-info.txt" << EOF
备份信息
==================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份目录: $BACKUP_DIR
源目录: $SOURCE_DIR
备份内容:
- 配置文件 (openclaw.json)
- 记忆系统 (memory/)
- 规则文件 (rules/)
- 任务管理 (tasks/)
- 脚本工具 (scripts/)
- 日志文件 (logs/, 最近7天)

备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)
文件数量: $(find "$BACKUP_DIR" -type f | wc -l)
==================================
EOF

echo "📄 创建备份信息文件" | tee -a "$LOG_FILE"

# 计算备份大小
backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
file_count=$(find "$BACKUP_DIR" -type f | wc -l)

echo "✅ 备份完成!" | tee -a "$LOG_FILE"
echo "   备份大小: $backup_size" | tee -a "$LOG_FILE"
echo "   文件数量: $file_count" | tee -a "$LOG_FILE"

# GitHub备份提醒
echo "" | tee -a "$LOG_FILE"
# 清理旧备份（保留最近7天）
echo "🧹 清理旧备份..." | tee -a "$LOG_FILE"
find "$BACKUP_BASE_DIR" -name "backup-*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null && echo "   ✅ 已清理7天前的备份" | tee -a "$LOG_FILE" || echo "   ❌ 清理旧备份失败" | tee -a "$LOG_FILE"

echo "📤 GitHub备份提醒:" | tee -a "$LOG_FILE"
echo "   备份已完成到: $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "   请手动将以下内容推送到GitHub:" | tee -a "$LOG_FILE"
echo "   cd $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "   git init" | tee -a "$LOG_FILE"
echo "   git add ." | tee -a "$LOG_FILE"
echo "   git commit -m \"自动备份 $(date '+%Y-%m-%d %H:%M:%S')\"" | tee -a "$LOG_FILE"
echo "   git remote add origin git@github.com:$GITHUB_REPO.git" | tee -a "$LOG_FILE"
echo "   git push -u origin main" | tee -a "$LOG_FILE"

# 记录结束时间
echo "" | tee -a "$LOG_FILE"
echo "⏰ 备份结束: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 显示结果
echo ""
echo "🔄 备份完成!"
echo "   备份目录: $BACKUP_DIR"
echo "   基础目录: $BACKUP_BASE_DIR"
echo "   备份大小: $backup_size"
echo "   文件数量: $file_count"
echo "   日志文件: $LOG_FILE"
echo "   自动清理: 保留最近7天备份"
echo ""
echo "📤 请记得手动备份到GitHub!"
echo "   查看日志: tail -f $LOG_FILE"