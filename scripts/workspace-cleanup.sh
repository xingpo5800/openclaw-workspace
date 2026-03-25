#!/bin/bash
# workspace临时文件清理脚本
# 每两天执行一次，删除projects/media/下超过48小时的临时文件
# 保留后悔窗口

WS="/Users/kevin/.openclaw/workspace"
MEDIA="$WS/projects/media"

if [ -d "$MEDIA" ]; then
    # 删除48小时前的临时文件（test_/tmp_/v*s等）
    find "$MEDIA" -maxdepth 1 -type f \
        \( -name "test_*" -o -name "tmp_*" -o -name "frame_*" -o -name "v*s*" -o -name "s*s.png" -o -name "sc*" \) \
        -mmin +2880 -delete 2>/dev/null
    
    # 删除根目录下的临时图片（万一有残留）
    find "$WS" -maxdepth 1 -type f \
        \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) \
        -mmin +2880 -delete 2>/dev/null
    
    echo "$(date): workspace清理完成"
fi
