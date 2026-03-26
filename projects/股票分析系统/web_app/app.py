"""
灵犀量化分析 Web 服务
运行: python app.py
访问: http://localhost:5151
"""

import os
import json
import threading
import time
import uuid
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULT_DIR = os.path.join(WEB_APP_DIR, "results")
QUEUE_FILE = os.path.join(WEB_APP_DIR, "analysis_queue.json")
TASKS_FILE = os.path.join(WEB_APP_DIR, "analysis_tasks.json")

os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

def enqueue_analysis(stock_code, stock_name, task_id):
    """加入分析队列（文件队列方式）"""
    queue = load_queue()
    queue.append({
        "task_id": task_id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "enqueued_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_queue(queue)
    
    # 启动分析器进程（如果还没在跑）
    import subprocess
    pid_file = os.path.join(WEB_APP_DIR, "analyzer.pid")
    try:
        if os.path.exists(pid_file):
            pid = int(open(pid_file).read().strip())
            os.kill(pid, 0)  # 进程存在则不重复启动
        else:
            raise FileNotFoundError
    except:
        # 分析器未运行，启动它
        subprocess.Popen(
            ["python3", os.path.join(WEB_APP_DIR, "analyzer.py")],
            cwd=WEB_APP_DIR,
            stdout=open(os.path.join(WEB_APP_DIR, "analyzer_stderr.log"), "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tracking-pool")
def get_tracking_pool():
    portfolio_file = os.path.join(PROJECT_ROOT, "portfolio.json")
    if os.path.exists(portfolio_file):
        with open(portfolio_file, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route("/api/analyze", methods=["POST"])
def trigger_analysis():
    data = request.json
    stock_code = data.get("stock_code", "").strip()
    stock_name = data.get("stock_name", "").strip()
    
    if not stock_code:
        return jsonify({"error": "股票代码不能为空"}), 400
    
    task_id = str(uuid.uuid4())[:8]
    
    tasks = load_tasks()
    tasks[task_id] = {
        "task_id": task_id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "status": "queued",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "result": None
    }
    save_tasks(tasks)
    
    # 加入队列，由 analyzer 处理
    enqueue_analysis(stock_code, stock_name, task_id)
    
    return jsonify({
        "task_id": task_id,
        "status": "queued",
        "message": f"已加入队列 {stock_name}，灵犀正在准备分析..."
    })

@app.route("/api/result/<task_id>")
def get_result(task_id):
    tasks = load_tasks()
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)

@app.route("/api/tasks")
def list_tasks():
    tasks = load_tasks()
    items = sorted(tasks.values(), key=lambda x: x.get("created_at", ""), reverse=True)[:15]
    return jsonify(items)

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "time": time.strftime("%H:%M:%S")})

if __name__ == "__main__":
    print("🦏 灵犀量化分析 Web 服务启动中...")
    print(f"📊 项目目录: {PROJECT_ROOT}")
    print(f"🌐 访问地址: http://localhost:5151")
    print(f"🔧 分析队列: {QUEUE_FILE}")
    app.run(host="0.0.0.0", port=5151, debug=False, threaded=True)
