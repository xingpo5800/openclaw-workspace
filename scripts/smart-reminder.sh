#!/bin/bash
# OpenClaw 智能提醒系统

# 配置
LOG_FILE="/Users/kevin/.openclaw/workspace/logs/smart-reminder-$(date +%Y-%m-%d).log"
ALERT_FILE="/Users/kevin/.openclaw/workspace/logs/alerts-$(date +%Y-%m-%d).txt"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "==================================" | tee -a "$LOG_FILE"
echo "🔔 开始智能提醒检查: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 清空今日提醒文件
> "$ALERT_FILE"

# 检查函数
check_and_alert() {
    local category="$1"
    local message="$2"
    local priority="$3"  # high|medium|low
    
    echo "🔍 检查 $category..." | tee -a "$LOG_FILE"
    
    # 根据不同类型进行检查
    case "$category" in
        "tasks")
            check_tasks "$message" "$priority"
            ;;
        "rules")
            check_rules "$message" "$priority"
            ;;
        "backup")
            check_backup "$message" "$priority"
            ;;
        "system")
            check_system "$message" "$priority"
            ;;
        "memory")
            check_memory "$message" "$priority"
            ;;
    esac
}

# 任务检查
check_tasks() {
    local message="$1"
    local priority="$2"
    
    # 检查高优先级待办任务
    high_priority_tasks=$(find /Users/kevin/.openclaw/workspace/tasks/todo -name "*.md" -exec grep -l "high" {} \; 2>/dev/null | wc -l)
    
    if [ "$high_priority_tasks" -gt 0 ]; then
        echo "⚠️  发现 $high_priority_tasks 个高优先级待办任务!" | tee -a "$LOG_FILE"
        echo "📋 高优先级任务提醒:" >> "$ALERT_FILE"
        find /Users/kevin/.openclaw/workspace/tasks/todo -name "*.md" -exec grep -l "high" {} \; | while read task; do
            task_name=$(basename "$task" .md)
            echo "   - $task_name" >> "$ALERT_FILE"
        done
        echo "" >> "$ALERT_FILE"
    fi
    
    # 检查是否有任务超过3天未处理
    find /Users/kevin/.openclaw/workspace/tasks/todo -name "*.md" -mtime +3 | while read task; do
        task_name=$(basename "$task" .md)
        echo "⏰ 任务 '$task_name' 超过3天未处理!" | tee -a "$LOG_FILE"
        echo "⏰ 任务 '$task_name' 超过3天未处理!" >> "$ALERT_FILE"
    done
}

# 规则检查
check_rules() {
    local message="$1"
    local priority="$2"
    
    # 检查规则索引完整性
    rules_count=$(ls /Users/kevin/.openclaw/workspace/rules/*.md 2>/dev/null | wc -l)
    indexed_count=$(grep -E "^[[:space:]]*- .*\.md" /Users/kevin/.openclaw/workspace/memory/rules-index.md | wc -l)
    
    if [ "$rules_count" -ne "$indexed_count" ]; then
        echo "⚠️  规则索引可能不完整: $rules_count 个规则文件, $indexed_count 个索引引用" | tee -a "$LOG_FILE"
        echo "📜 规则索引不完整提醒:" >> "$ALERT_FILE"
        echo "   规则文件数量: $rules_count" >> "$ALERT_FILE"
        echo "   索引引用数量: $indexed_count" >> "$ALERT_FILE"
        echo "" >> "$ALERT_FILE"
    fi
    
    # 检查是否有规则未进行审查
    recent_reviews=$(find /Users/kevin/.openclaw/workspace/memory/rules -name "*rule-review*" -mtime -7 | wc -l)
    if [ "$recent_reviews" -eq 0 ]; then
        echo "⚠️  最近无规则审查记录!" | tee -a "$LOG_FILE"
        echo "🔍 规则审查提醒:" >> "$ALERT_FILE"
        echo "   建议定期进行规则审查" >> "$ALERT_FILE"
        echo "" >> "$ALERT_FILE"
    fi
}

# 备份检查
check_backup() {
    local message="$1"
    local priority="$2"
    
    # 检查今天是否已经备份
    today_backup="/Volumes/data-backup/openclawbackup/backup-$(date +%Y-%m-%d)"
    if [ ! -d "$today_backup" ]; then
        echo "⚠️  今天还没有执行备份!" | tee -a "$LOG_FILE"
        echo "💾 备份提醒:" >> "$ALERT_FILE"
        echo "   今天还未执行备份" >> "$ALERT_FILE"
        echo "   建议检查备份脚本是否正常运行" >> "$ALERT_FILE"
        echo "" >> "$ALERT_FILE"
    else
        echo "✅ 今日备份已完成" | tee -a "$LOG_FILE"
    fi
    
    # 检查GitHub备份状态
    if [ -d "$today_backup/.git" ]; then
        push_status=$(cd "$today_backup" && git log --oneline -1 2>/dev/null)
        if [ -n "$push_status" ]; then
            echo "✅ GitHub备份已同步" | tee -a "$LOG_FILE"
        else
            echo "⚠️  GitHub备份未同步!" | tee -a "$LOG_FILE"
            echo "🚀 GitHub备份提醒:" >> "$ALERT_FILE"
            echo "   备份已完成但未推送到GitHub" >> "$ALERT_FILE"
            echo "" >> "$ALERT_FILE"
        fi
    fi
}

# 系统检查
check_system() {
    local message="$1"
    local priority="$2"
    
    # 检查磁盘空间
    disk_usage=$(df /Volumes/data-backup | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        echo "⚠️  备份磁盘空间使用率过高: ${disk_usage}%" | tee -a "$LOG_FILE"
        echo "💿 磁盘空间提醒:" >> "$ALERT_FILE"
        echo "   备份磁盘使用率: ${disk_usage}%" >> "$ALERT_FILE"
        echo "   建议清理旧备份文件" >> "$ALERT_FILE"
        echo "" >> "$ALERT_FILE"
    fi
    
    # 检查内存使用
    memory_usage=$(top -l 1 -n 0 | grep "PhysMem" | awk '{print $2}' | sed 's/.*://')
    echo "💾 内存使用情况: $memory_usage" | tee -a "$LOG_FILE"
}

# 记忆检查
check_memory() {
    local message="$1"
    local priority="$2"
    
    # 检查MEMORY.md大小
    memory_size=$(wc -l < /Users/kevin/.openclaw/workspace/MEMORY.md)
    if [ "$memory_size" -gt 50 ]; then
        echo "⚠️  MEMORY.md 可能存在冗余内容 ($memory_size 行)" | tee -a "$LOG_FILE"
        echo "📝 记忆文件提醒:" >> "$ALERT_FILE"
        echo "   MEMORY.md 大小: $memory_size 行" >> "$ALERT_FILE"
        echo "   建议清理冗余内容" >> "$ALERT_FILE"
        echo "" >> "$ALERT_FILE"
    fi
}

# 执行所有检查
echo "🔍 开始执行智能检查..." | tee -a "$LOG_FILE"

check_and_alert "tasks" "任务状态检查" "high"
check_and_alert "rules" "规则体系检查" "medium"
check_and_alert "backup" "备份状态检查" "high"
check_and_alert "system" "系统状态检查" "medium"
check_and_alert "memory" "记忆系统检查" "low"

# 检查是否有提醒
if [ -s "$ALERT_FILE" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "📢 今日提醒事项:" | tee -a "$LOG_FILE"
    echo "==================================" | tee -a "$LOG_FILE"
    cat "$ALERT_FILE" | tee -a "$LOG_FILE"
    
    # 如果有高优先级提醒，发送桌面通知
    if grep -q "⚠️" "$ALERT_FILE"; then
        echo "" | tee -a "$LOG_FILE"
        echo "🔔 有高优先级提醒需要关注!" | tee -a "$LOG_FILE"
    fi
else
    echo "" | tee -a "$LOG_FILE"
    echo "✅ 所有检查正常，无提醒事项!" | tee -a "$LOG_FILE"
fi

# 记录结束时间
echo "" | tee -a "$LOG_FILE"
echo "⏰ 智能提醒检查完成: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# 显示结果
echo ""
echo "🔔 智能提醒检查完成!"
echo "   日志文件: $LOG_FILE"
echo "   提醒文件: $ALERT_FILE"
echo ""

# 如果有提醒内容，显示摘要
if [ -s "$ALERT_FILE" ]; then
    echo "📢 今日提醒事项:"
    echo "=================================="
    cat "$ALERT_FILE"
    echo "=================================="
else
    echo "✅ 所有检查正常，无提醒事项!"
fi