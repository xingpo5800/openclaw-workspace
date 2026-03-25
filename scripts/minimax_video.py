#!/usr/bin/env python3
"""
MiniMax 海螺AI 视频生成工具
用法：
  python3 minimax_video.py "一只猫在弹吉他" [时长] [分辨率]
  python3 minimax_video.py "输入提示词" --duration 6 --resolution 768P

示例：
  python3 minimax_video.py "A programmer at a desk, coding late at night, glowing screen light" 6 768P
  python3 minimax_video.py "古风美女在桃花树下抚琴" 10 1080P
"""

import requests
import json
import time
import sys
import os
import argparse

# ============ 配置区 ============
# API Key 从环境变量或配置文件读取
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = "https://api.minimax.io"

# 默认参数
DEFAULT_DURATION = 6
DEFAULT_RESOLUTION = "768P"
DEFAULT_MODEL = "MiniMax-Hailuo-02"  # 性价比最高，支持10s


def create_video(prompt: str, duration: int = DEFAULT_DURATION,
                 resolution: str = DEFAULT_RESOLUTION,
                 model: str = DEFAULT_MODEL) -> str:
    """创建视频生成任务，返回 task_id"""
    url = f"{BASE_URL}/v1/video_generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "prompt_optimizer": True
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    data = resp.json()

    if data.get("base_resp", {}).get("status_code", -1) != 0:
        raise Exception(f"创建任务失败: {data}")

    task_id = data["task_id"]
    print(f"✅ 任务已创建: {task_id}")
    return task_id


def query_status(task_id: str) -> dict:
    """查询任务状态"""
    url = f"{BASE_URL}/v1/query/video_generation"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"task_id": task_id}

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    return resp.json()


def wait_for_video(task_id: str, poll_interval: int = 5, max_wait: int = 300) -> dict:
    """轮询等待视频生成完成"""
    print(f"⏳ 等待生成中（每{poll_interval}秒查询一次）...")
    start = time.time()

    while time.time() - start < max_wait:
        result = query_status(task_id)
        status = result.get("status", "Unknown")

        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] 状态: {status}")

        if status == "Success":
            file_id = result.get("file_id")
            width = result.get("video_width", "?")
            height = result.get("video_height", "?")
            print(f"✅ 视频生成成功! file_id={file_id}, 分辨率={width}x{height}")
            return result

        elif status == "Failed":
            raise Exception(f"视频生成失败: {result}")

        time.sleep(poll_interval)

    raise TimeoutError(f"等待超时（>{max_wait}秒）")


def download_video(file_id: str, output_path: str = "output.mp4") -> str:
    """下载生成的视频"""
    url = f"{BASE_URL}/v1/files/retrieve"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"file_id": file_id}

    resp = requests.get(url, headers=headers, params=params, timeout=60, stream=True)

    if resp.status_code != 200:
        raise Exception(f"下载失败: HTTP {resp.status_code}")

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size = os.path.getsize(output_path)
    print(f"✅ 视频已保存: {output_path} ({size/1024/1024:.2f} MB)")
    return output_path


def generate_video(prompt: str, duration: int = DEFAULT_DURATION,
                   resolution: str = DEFAULT_RESOLUTION,
                   model: str = DEFAULT_MODEL,
                   output_path: str = "output.mp4",
                   poll_interval: int = 5) -> str:
    """一键生成视频：创建→等待→下载"""
    if not API_KEY:
        raise Exception("未设置 MINIMAX_API_KEY 环境变量")

    print(f"🎬 开始生成视频")
    print(f"  提示词: {prompt}")
    print(f"  时长: {duration}s | 分辨率: {resolution} | 模型: {model}")

    task_id = create_video(prompt, duration, resolution, model)
    result = wait_for_video(task_id, poll_interval)
    file_id = result["file_id"]
    path = download_video(file_id, output_path)

    print(f"\n🎉 完成！视频路径: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="MiniMax 海螺AI 视频生成")
    parser.add_argument("prompt", nargs="?", help="视频描述提示词")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                        help=f"视频时长(秒): 6或10, 默认{DEFAULT_DURATION}")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION,
                        choices=["720P", "768P", "1080P"],
                        help=f"分辨率, 默认{DEFAULT_RESOLUTION}")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"模型, 默认{DEFAULT_MODEL}")
    parser.add_argument("--output", "-o", default="output.mp4",
                        help="输出文件路径")
    parser.add_argument("--poll", type=int, default=5,
                        help="查询间隔(秒)")

    args = parser.parse_args()

    if not args.prompt:
        print(__doc__)
        print("\n示例用法:")
        print('  python3 minimax_video.py "一只猫在弹吉他"')
        print('  python3 minimax_video.py "程序员深夜coding" --duration 10 --resolution 1080P')
        sys.exit(0)

    generate_video(
        prompt=args.prompt,
        duration=args.duration,
        resolution=args.resolution,
        model=args.model,
        output_path=args.output,
        poll_interval=args.poll
    )


if __name__ == "__main__":
    main()
