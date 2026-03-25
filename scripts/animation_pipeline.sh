#!/bin/bash
# 不正经AI研究室 · 动画合成流水线
# 使用FFmpeg合成视频片段+字幕+片头片尾

PROJECT_DIR="$HOME/Desktop/pixverse-output/ep01"
SCENES_DIR="$PROJECT_DIR/scenes"
OUTPUT_DIR="$PROJECT_DIR/final"
TEMP_DIR="$PROJECT_DIR/temp"
WORKFILE="$TEMP_DIR/worklist.txt"

mkdir -p "$OUTPUT_DIR" "$TEMP_DIR"

echo "🎬 不正经AI研究室 · 动画合成开始"
echo "=================================="

# 片段列表：(文件路径, 标题, 副标题)
declare -a SCENES=(
    "$SCENES_DIR/scene01_diyafu.mp4|地府排队|转世投胎第一关，排队三年零六个月"
    "$SCENES_DIR/scene02_yanwangdian.mp4|阎王殿抽SSR|金光一闪——三千年没出过的SSR！"
    "$SCENES_DIR/scene03_mengpo.mp4|孟婆汤|这配方科学吗？能吃就行啦靓仔"
    "$SCENES_DIR/scene04_zhuge.mp4|出租屋|刷了一天短视频，越刷越迷茫……"
)

# 清空工作文件
> "$WORKFILE"

# 生成片段
for i in "${!SCENES[@]}"; do
    IFS='|' read -r video title subtitle <<< "${SCENES[$i]}"
    scene_num=$((i + 1))
    
    if [ ! -f "$video" ]; then
        echo "⚠️  场景不存在: $video"
        continue
    fi
    
    output="$TEMP_DIR/scene${scene_num}.mp4"
    echo "📹 [$scene_num/4] 处理: $title"
    
    # 生成字幕文件
    cat > "$TEMP_DIR/sub_${scene_num}.ass" << EOF
[Script Info]
Title: 字幕
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,Arial,36,&H00FFFFFF,&H00000000,-1,0,1,2,0,2,10,10,20

[Events]
Format: Layer, Start, End, Style, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,$title
Dialogue: 0,0:00:00.00,0:00:05.00,Default,$subtitle
EOF
    
    # 合成视频+字幕
    ffmpeg -y -i "$video" -vf "ass=$TEMP_DIR/sub_${scene_num}.ass" \
        -c:v libx264 -preset fast -crf 23 \
        -c:a aac -b:a 128k \
        -an \
        "$output" 2>/dev/null
    
    if [ -f "$output" ]; then
        echo "  ✅ 完成 ($title)"
        echo "file '$output'" >> "$WORKFILE"
    fi
done

echo ""
echo "🔗 连接所有片段..."

# 生成片头（纯色+文字）
ffmpeg -y -f lavfi -i "color=c=black:s=1280x720:d=3" \
    -vf "drawtext=text='不正经AI研究室':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-30,drawtext=text='第一集：转世投胎':fontsize=40:fontcolor=cyan:x=(w-text_w)/2:y=(h-text_h)/2+30" \
    -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
    "$TEMP_DIR/intro.mp4" 2>/dev/null

# 生成片尾
ffmpeg -y -f lavfi -i "color=c=black:s=1280x720:d=3" \
    -vf "drawtext=text='下期预告：相杀相爱正式开始':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h/2-30,drawtext=text='关注「不正经AI研究室」':fontsize=28:fontcolor=cyan:x=(w-text_w)/2:y=h/2+30" \
    -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
    "$TEMP_DIR/outro.mp4" 2>/dev/null

# 把片头和片尾加入工作列表
echo "file '$TEMP_DIR/intro.mp4'" | cat - "$WORKFILE" > "$TEMP_DIR/worklist_with_io.txt"
echo "file '$TEMP_DIR/outro.mp4'" >> "$TEMP_DIR/worklist_with_io.txt"

# 连接所有片段
echo ""
echo "🎞️  最终合成..."
ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/worklist_with_io.txt" \
    -c:v libx264 -preset fast -crf 20 \
    -c:a aac -b:a 128k \
    "$OUTPUT_DIR/EP01_final.mp4" 2>/dev/null

if [ -f "$OUTPUT_DIR/EP01_final.mp4" ]; then
    SIZE=$(ls -lh "$OUTPUT_DIR/EP01_final.mp4" | awk '{print $5}')
    echo ""
    echo "✅ 合成完成！"
    echo "📁 文件: $OUTPUT_DIR/EP01_final.mp4"
    echo "📊 大小: $SIZE"
else
    echo "❌ 合成失败"
fi

echo ""
echo "🧹 清理临时文件..."
rm -rf "$TEMP_DIR"
echo "✅ 完成"
