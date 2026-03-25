#!/bin/bash
# 语音播报工具
# 用法: ./voice.sh "要说的内容"

TEXT="$1"
if [ -z "$TEXT" ]; then
    echo "用法: ./voice.sh \"要说的内容\""
    exit 1
fi

say -v "Ting-Ting" "$TEXT"
