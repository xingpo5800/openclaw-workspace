#!/bin/bash
# 规则执行检查脚本

echo "🔍 规则执行检查 - $(date '+%Y-%m-%d %H:%M')"
echo "=================================="

# 检查规则索引完整性
echo "📋 检查规则索引完整性..."
rules_count=$(ls /Users/kevin/.openclaw/workspace/rules/*.md 2>/dev/null | wc -l)
indexed_count=$(grep -E "^[[:space:]]*- .*\.md" /Users/kevin/.openclaw/workspace/memory/rules-index.md | wc -l)

echo "  规则文件数量: $rules_count"
echo "  索引引用数量: $indexed_count"

if [ "$rules_count" -ne "$indexed_count" ]; then
    echo "  ⚠️  规则索引可能不完整"
else
    echo "  ✅ 规则索引完整"
fi

# 检查MEMORY.md冗余
echo ""
echo "📄 检查MEMORY.md冗余..."
memory_size=$(wc -l < /Users/kevin/.openclaw/workspace/MEMORY.md)
if [ "$memory_size" -gt 50 ]; then
    echo "  ⚠️  MEMORY.md可能存在冗余内容 ($memory_size 行)"
else
    echo "  ✅ MEMORY.md大小正常 ($memory_size 行)"
fi

# 检查任务管理工具使用
echo ""
echo "📋 检查任务管理工具使用..."
todo_count=$(ls /Users/kevin/.openclaw/workspace/tasks/todo/*.md 2>/dev/null | wc -l)
doing_count=$(ls /Users/kevin/.openclaw/workspace/tasks/doing/*.md 2>/dev/null | wc -l)
done_count=$(ls /Users/kevin/.openclaw/workspace/tasks/done/*.md 2>/dev/null | wc -l)

echo "  待办任务: $todo_count"
echo "  正在任务: $doing_count"
echo "  已完成任务: $done_count"

# 检查最近是否有新规则
echo ""
echo "📝 检查最近新增规则..."
recent_rules=$(find /Users/kevin/.openclaw/workspace/rules -name "*.md" -mtime -7 | head -5)
if [ -n "$recent_rules" ]; then
    echo "  最近新增规则:"
    echo "$recent_rules" | while read rule; do
        echo "    - $(basename "$rule")"
    done
else
    echo "  ✅ 最近无新规则"
fi

# 检查规则审查状态
echo ""
echo "🔍 检查规则审查状态..."
recent_reviews=$(find /Users/kevin/.openclaw/workspace/memory/rules -name "*rule-review*" -mtime -7 | head -3)
if [ -n "$recent_reviews" ]; then
    echo "  最近审查记录:"
    echo "$recent_reviews" | while read review; do
        echo "    - $(basename "$review")"
    done
else
    echo "  ⚠️  最近无规则审查记录"
fi

echo ""
echo "=================================="
echo "💡 建议:"
echo "  1. 定期运行此检查脚本"
echo "  2. 发现问题及时修复"
echo "  3. 保持规则体系的完整性"
echo "=================================="