#!/usr/bin/env python3
"""
不正经AI研究室 · 动画合成流水线 v2
用Pillow生成字幕图像 + FFmpeg合成
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HOME = Path.home()
PROJECT_DIR = HOME / "Desktop" / "pixverse-output" / "ep01"
SCENES_DIR = PROJECT_DIR / "scenes"
OUTPUT_DIR = PROJECT_DIR / "final"
TEMP_DIR = PROJECT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

def run(cmd, desc=""):
    """执行命令"""
    print(f"  {'⚙️' if desc else '→'} {desc or '执行'}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and "Error" not in result.stderr and "error" not in result.stderr:
        pass  # ffmpeg输出很多info不算error
    return result.returncode == 0

def create_intro(width=1280, height=720, duration=3):
    """生成片头"""
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 60)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
    except:
        font_title = font_sub = ImageFont.load_default()
    
    # 主标题
    draw.text((width//2, height//2 - 40), "不正经AI研究室", 
               fill='white', font=font_title, anchor='mm')
    # 副标题
    draw.text((width//2, height//2 + 30), "第一集：转世投胎", 
               fill='cyan', font=font_sub, anchor='mm')
    
    img.save(TEMP_DIR / "intro.png")
    return True

def create_outro(width=1280, height=720, duration=3):
    """生成片尾"""
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except:
        font_title = font_sub = ImageFont.load_default()
    
    draw.text((width//2, height//2 - 30), "下期预告：相杀相爱正式开始", 
               fill='white', font=font_title, anchor='mm')
    draw.text((width//2, height//2 + 20), "关注「不正经AI研究室」", 
               fill='cyan', font=font_sub, anchor='mm')
    
    img.save(TEMP_DIR / "outro.png")
    return True

def make_video_from_image(img_path, output, duration=3, fps=24):
    """把图片转成视频"""
    cmd = f'ffmpeg -y -loop 1 -i "{img_path}" -t {duration} -vf "fps={fps},scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -preset fast -pix_fmt yuv420p "{output}"'
    return run(cmd)

def scale_to_720p(input_video, output_video):
    """统一缩放到720p"""
    cmd = f'ffmpeg -y -i "{input_video}" -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1" -c:v libx264 -preset fast -crf 23 -c:a copy "{output_video}"'
    return run(cmd)

def add_subtitle(input_video, title, subtitle, output_video):
    """用Pillow生成字幕图片叠加"""
    # 生成字幕背景图
    sub_img = Image.new('RGBA', (1280, 100), (0, 0, 0, 180))
    draw = ImageDraw.Draw(sub_img)
    
    try:
        font1 = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
        font2 = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except:
        font1 = font2 = ImageFont.load_default()
    
    draw.text((20, 10), title, fill='white', font=font1)
    draw.text((20, 55), subtitle, fill='lightgray', font=font2)
    sub_img.save(TEMP_DIR / "subtitle_bg.png")
    
    # 用FFmpeg叠加
    cmd = f'''ffmpeg -y -i "{input_video}" -i "{TEMP_DIR / "subtitle_bg.png"}" \
        -filter_complex "[0:v][1:v]overlay=0:H-100:format=auto" \
        -c:v libx264 -preset fast -crf 23 -c:a copy "{output_video}"'''
    return run(cmd)

def main():
    print("🎬 不正经AI研究室 · 动画合成")
    print("=" * 40)
    
    # 生成片头片尾
    print("\n📝 生成片头...")
    create_intro()
    make_video_from_image(TEMP_DIR / "intro.png", TEMP_DIR / "intro.mp4")
    
    print("📝 生成片尾...")
    create_outro()
    make_video_from_image(TEMP_DIR / "outro.png", TEMP_DIR / "outro.mp4")
    
    # 场景列表
    scenes = [
        (SCENES_DIR / "scene01_diyafu.mp4", "地府排队", "转世投胎第一关，排队三年零六个月"),
        (SCENES_DIR / "scene02_yanwangdian.mp4", "阎王殿抽SSR", "金光一闪——三千年没出过的SSR！"),
        (SCENES_DIR / "scene03_mengpo.mp4", "孟婆汤", "这配方科学吗？能吃就行啦靓仔"),
        (SCENES_DIR / "scene04_zhuge.mp4", "出租屋", "刷了一天短视频，越刷越迷茫……"),
    ]
    
    # 处理每个场景
    for i, (scene_path, title, subtitle) in enumerate(scenes, 1):
        if not scene_path.exists():
            print(f"  ⚠️  跳过: {scene_path} 不存在")
            continue
        
        scaled = TEMP_DIR / f"scene{i}_scaled.mp4"
        with_sub = TEMP_DIR / f"scene{i}_sub.mp4"
        
        print(f"\n📹 [$i/4] {title}")
        
        # 缩放到720p
        ok1 = scale_to_720p(scene_path, scaled)
        if not ok1:
            print(f"  ⚠️  缩放失败，尝试直接复制")
            import shutil
            shutil.copy(scene_path, scaled)
        
        # 加字幕
        ok2 = add_subtitle(scaled, title, subtitle, with_sub)
        if ok2:
            print(f"  ✅ 完成")
        else:
            # 字幕失败就用没字幕的
            import shutil
            shutil.copy(scaled, with_sub)
            print(f"  ⚠️  字幕失败，使用无字幕版本")
    
    # 生成concat列表
    list_file = TEMP_DIR / "concat.txt"
    with open(list_file, 'w') as f:
        f.write(f"file '{TEMP_DIR}/intro.mp4'\n")
        for i in range(1, 5):
            scene_file = TEMP_DIR / f"scene{i}_sub.mp4"
            if scene_file.exists():
                f.write(f"file '{scene_file}'\n")
        f.write(f"file '{TEMP_DIR}/outro.mp4'\n")
    
    # 连接
    print("\n🔗 连接片段...")
    output_file = OUTPUT_DIR / "EP01_final.mp4"
    cmd = f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{output_file}"'
    ok = run(cmd, "合成最终视频")
    
    if ok and output_file.exists():
        size = output_file.stat().st_size / 1024 / 1024
        print(f"\n✅ 合成完成！")
        print(f"📁 {output_file}")
        print(f"📊 {size:.1f} MB")
    else:
        print(f"\n❌ 合成失败")
    
    # 清理
    print("\n🧹 清理临时文件...")
    import shutil
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print("✅ 完成")

if __name__ == "__main__":
    main()
