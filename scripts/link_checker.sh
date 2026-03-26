#!/bin/bash
# 修改文件后自动检查关联文件
# 用法：在 git commit 后运行，或手动运行

echo "=== 关联文件检查 ==="

# 获取今天修改的文件
today=$(date "+%Y-%m-%d")
modified=$(cd ~/.openclaw/workspace && git diff --name-only HEAD 2>/dev/null)

if [ -z "$modified" ]; then
    echo "没有文件变更"
    exit 0
fi

echo "今天修改的文件："
echo "$modified"
echo

# 定义关联规则（不用规则，用数据）
declare -A links=(
    ["memory/core-memory.md"]="MEMORY.md,memory/knowledge-map.md"
    ["MEMORY.md"]="memory/knowledge-map.md,AGENTS.md"
    ["AGENTS.md"]="memory/knowledge-map.md"
    ["memory/knowledge-map.md"]="MEMORY.md,AGENTS.md"
    ["rules/system-rules.md"]="MEMORY.md,AGENTS.md,rules/rules-index.md"
    ["rules/rules-index.md"]="MEMORY.md,AGENTS.md"
    ["memory/today.md"]="MEMORY.md,memory/knowledge-map.md"
    ["memory/predictions.md"]="MEMORY.md,memory/knowledge-map.md"
    ["memory/训练规划.md"]="MEMORY.md,memory/knowledge-map.md"
    ["memory/进化规划.md"]="MEMORY.md,memory/knowledge-map.md"
)

# 检查关联
echo "需要同步检查的文件："
needs_update=0
for file in $modified; do
    if [ -n "${links[$file]}" ]; then
        echo "  $file → 需要检查: ${links[$file]}"
        needs_update=1
    fi
done

if [ "$needs_update" = "0" ]; then
    echo "  无需额外检查 ✅"
fi

echo
echo "=== 建议：修改后主动检查以上文件是否需要同步更新 ==="
