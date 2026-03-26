#!/usr/bin/env python3
"""
灵犀分析器 - 监听分析队列，触发 OpenClaw 执行分析
"""

import os
import sys
import json
import time
import uuid
import subprocess

WEB_APP_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(WEB_APP_DIR, "results")
QUEUE_FILE = os.path.join(WEB_APP_DIR, "analysis_queue.json")
TASKS_FILE = os.path.join(WEB_APP_DIR, "analysis_tasks.json")
PID_FILE = os.path.join(WEB_APP_DIR, "analyzer.pid")
LOG_FILE = os.path.join(WEB_APP_DIR, "analyzer.log")

os.makedirs(RESULT_DIR, exist_ok=True)

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except: pass

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE) as f:
                return json.load(f)
        except: pass
    return []

def save_queue(q):
    with open(QUEUE_FILE, "w") as f:
        json.dump(q, f, ensure_ascii=False, indent=2)

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE) as f:
                return json.load(f)
        except: pass
    return {}

def save_tasks(t):
    with open(TASKS_FILE, "w") as f:
        json.dump(t, f, ensure_ascii=False, indent=2)

def update_task(task_id, status, result=None, error=None):
    tasks = load_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = status
        tasks[task_id]["done_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if result:
            tasks[task_id]["result"] = result
        if error:
            tasks[task_id]["error"] = error
    save_tasks(tasks)

def trigger_openclaw(stock_code, stock_name, task_id, prompt):
    """base64 编码 message，bash 解码后传给 --message，彻底避免引号转义"""
    import base64
    session_id = f"a-{task_id}-{uuid.uuid4().hex[:8]}"
    log_file = os.path.join(WEB_APP_DIR, f"log_{task_id}.txt")
    msg_b64 = base64.b64encode(prompt.encode("utf-8")).decode("ascii")
    
    # bash -c: base64 解码后通过临时变量传给 openclaw --message
    cmd = (
        f'MSG=$(echo {msg_b64} | base64 -d) && '
        f'openclaw agent --session-id {session_id} --timeout 120 --message "$MSG" > {log_file} 2>&1'
    )
    
    proc = subprocess.Popen(
        ["bash", "-c", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        cwd=os.path.expanduser("~/.openclaw/workspace/projects/股票分析系统")
    )
    log(f"🔔 openclaw agent 已触发 (session={session_id}, pid={proc.pid})")
    return session_id

def run_analysis(stock_code, stock_name, task_id):
    result_file = os.path.join(RESULT_DIR, f"{task_id}.json")
    
    prompt = f"""请对 {stock_name}（代码：{stock_code}）进行5分钟、15分钟、30分钟、日线四个级别的深度缠论+蜡烛图+量价分析。

分析步骤：
1. 读取K线数据（5分钟/15分钟/30分钟/日线）
2. 执行缠论分析（笔/中枢/背驰/分型/买卖点）
3. 执行蜡烛图分析（形态/反转信号）
4. 执行量价分析（5日均量/60日均量/量能斜率）
5. 四维打分（缠论/蜡烛图/量价/真技术各10分）
6. 给出综合建议

完成后将结果写入文件：{result_file}

结果JSON格式：
{{
  "stock_code": "{stock_code}",
  "stock_name": "{stock_name}",
  "timestamp": "<分析时间>",
  "analysis": {{
    "5分钟": {{"笔数":0,"中枢":0,"背驰":"无","分型":"底分型","买卖点":"1买","评分":0}},
    "15分钟": {{"笔数":0,"中枢":0,"背驰":"无","分型":"底分型","买卖点":"1买","评分":0}},
    "30分钟": {{"笔数":0,"中枢":0,"背驰":"无","分型":"底分型","买卖点":"1买","评分":0}},
    "日线": {{"笔数":0,"中枢":0,"背驰":"无","分型":"底分型","买卖点":"1买","评分":0}}
  }},
  "四维总分": 0,
  "建议": "买入",
  "止损": "0.00",
  "目标": "0.00",
  "简报": "一段话总结"
}}
"""
    
    log(f"📊 开始分析 {stock_name}({stock_code})，task_id={task_id}")
    update_task(task_id, "running")
    
    session_id = trigger_openclaw(stock_code, stock_name, task_id, prompt)
    
    # 等待结果（最多120秒，每10秒检查一次）
    for i in range(12):
        time.sleep(10)
        if os.path.exists(result_file):
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    analysis_result = json.load(f)
                update_task(task_id, "done", result=analysis_result)
                log(f"✅ {stock_name} 分析完成，四维总分={analysis_result.get('四维总分','?')}")
                return
            except Exception as e:
                log(f"⚠️ 读取结果失败: {e}")
        
        # 检查是否超时
        log_file = os.path.join(WEB_APP_DIR, f"log_{task_id}.txt")
        if os.path.exists(log_file):
            with open(log_file) as f:
                content = f.read()
            if "error" in content.lower() or "failed" in content.lower():
                log(f"⚠️ openclaw 输出了错误: {content[-200:]}")
    
    update_task(task_id, "timeout", error="等待结果超时（120秒）")
    log(f"⏰ {stock_name} 等待结果超时")

def process_queue():
    queue = load_queue()
    if not queue:
        return
    
    task = queue.pop(0)
    save_queue(queue)
    
    stock_code = task["stock_code"]
    stock_name = task["stock_name"]
    task_id = task["task_id"]
    
    run_analysis(stock_code, stock_name, task_id)

def main():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    log("🚀 灵犀分析器启动，监听队列...")
    
    while True:
        try:
            process_queue()
        except Exception as e:
            log(f"处理异常: {e}")
        
        time.sleep(3)

if __name__ == "__main__":
    main()
