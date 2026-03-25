#!/usr/bin/env python3
import subprocess, re, time, datetime, os

STOCKS = {
    'sz300830': ('金现代', 13.866),
    'sz002202': ('金风科技', 30.17),
    'sz002865': ('钧达股份', 84.77),
    'sh000001': ('上证指数', None)
}
LAST_REPORT_TIME = None
LAST_PRICE = {k: None for k in STOCKS}
CHECK_INTERVAL = 120  # 2分钟
REPORT_INTERVAL = 1800  # 30分钟

def fetch_data():
    try:
        r = subprocess.run(
            ['curl', '-s', 'https://qt.gtimg.cn/q=' + ','.join(STOCKS.keys())],
            capture_output=True, timeout=10
        )
        text = r.stdout.decode('gbk', errors='replace')
        data = {}
        for m in re.finditer(r'v_(\w+)="([^"]+)"', text):
            code = m.group(1)
            f = m.group(2).split('~')
            if len(f) > 4 and code in STOCKS:
                name = f[1]
                cur = float(f[3])
                prev = float(f[4])
                chg = (cur - prev) / prev * 100
                cost = STOCKS[code][1]
                pnl = (cur - cost) / cost * 100 if cost else None
                data[code] = {'name': name, 'cur': cur, 'chg': chg, 'pnl': pnl, 'cost': cost}
        return data
    except Exception as e:
        print(f"[{now()}] 获取数据失败: {e}")
        return {}

def say(text):
    subprocess.Popen(['say', '-v', 'Ting-Ting', text])
    print(f"[语音] {text}")

def now():
    return datetime.datetime.now().strftime('%H:%M')

def should_alert(data):
    """检查是否需要立即告警"""
    alerts = []
    for code, info in data.items():
        if code == 'sh000001':
            if abs(info['chg']) > 1:
                alerts.append(f"大盘{'上涨' if info['chg']>0 else '下跌'} {info['chg']:+.2f}%，超过1%阈值")
        else:
            if abs(info['chg']) > 2:
                alerts.append(f"{info['name']}涨跌 {info['chg']:+.2f}%，超过2%阈值")
            if info['cost'] and info['pnl'] < -5:
                alerts.append(f"{info['name']}已跌破成本价5%，当前亏损 {info['pnl']:.2f}%，逼近成本线！")
    return alerts

def format_report(data):
    lines = [f"📊 [{now()}] 持仓快报"]
    for code in ['sz002865', 'sz002202', 'sz300830']:
        if code in data:
            info = data[code]
            pnl_str = f" | 盈亏{info['pnl']:+.2f}%" if info['pnl'] is not None else ""
            lines.append(f"- {info['name']}：{info['cur']:.2f} {info['chg']:+.2f}%{pnl_str}")
    if 'sh000001' in data:
        idx = data['sh000001']
        lines.append(f"- 大盘：上证 {idx['cur']:.2f} {idx['chg']:+.2f}%")
    return '\n'.join(lines)

def check_price_change(data):
    """检查价格是否有明显变化（新价格与上次记录对比）"""
    global LAST_PRICE
    changes = []
    for code, info in data.items():
        if code == 'sh000001':
            prev = LAST_PRICE[code]
            if prev is not None:
                chg_pct = abs(info['cur'] - prev) / prev * 100
                if chg_pct > 0.5:
                    changes.append(f"大盘短线波动 {info['cur']:.2f}({info['chg']:+.2f}%)")
        else:
            prev = LAST_PRICE[code]
            if prev is not None:
                chg_pct = abs(info['cur'] - prev) / prev * 100
                if chg_pct > 1.0:
                    changes.append(f"{info['name']}短线变动 {info['cur']:.2f}({info['chg']:+.2f}%)")
    # 更新记录
    for code, info in data.items():
        LAST_PRICE[code] = info['cur']
    return changes

def main():
    global LAST_REPORT_TIME, LAST_PRICE

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_monitor.log')

    def log(msg):
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{ts}] {msg}"
        print(line)
        with open(log_path, 'a') as f:
            f.write(line + '\n')

    log("=== 股票监控启动 ===")
    for code, (name, cost) in STOCKS.items():
        if cost:
            log(f"  {name}({code}) 成本={cost}")

    LAST_REPORT_TIME = time.time()
    
    # 初始数据获取
    data = fetch_data()
    for code, info in data.items():
        LAST_PRICE[code] = info.get('cur')
    log(f"初始数据: {data}")

    while True:
        time.sleep(CHECK_INTERVAL)
        data = fetch_data()
        if not data:
            log("数据获取失败，重试...")
            continue

        now_ts = time.time()
        
        # 检查立即告警条件
        alerts = should_alert(data)
        if alerts:
            log(f"⚠️ 触发告警: {alerts}")
            say(" ".join(alerts))

        # 检查短线价格变动
        changes = check_price_change(data)
        
        # 30分钟例行播报
        if now_ts - LAST_REPORT_TIME >= REPORT_INTERVAL:
            report = format_report(data)
            log("=== 30分钟例行播报 ===")
            log(report)
            # 语音播报（简洁版）
            parts = []
            for code in ['sz002865', 'sz002202', 'sz300830']:
                if code in data:
                    info = data[code]
                    direction = "涨" if info['chg'] > 0 else "跌"
                    parts.append(f"{info['name']}{direction}{abs(info['chg']):.2f}%")
            if 'sh000001' in data:
                idx = data['sh000001']
                direction = "涨" if idx['chg'] > 0 else "跌"
                parts.append(f"大盘{'涨' if idx['chg']>0 else '跌'}{abs(idx['chg']):.2f}%")
            say("毅哥，30分钟持仓快报，" + "，".join(parts))
            LAST_REPORT_TIME = now_ts

        # 收盘检查（15:00后不再监控）
        cur_time = datetime.datetime.now()
        if cur_time.hour >= 15 and cur_time.minute >= 5:
            # 收盘总结
            log("=== 收盘总结 ===")
            summary = format_report(data)
            log(summary)
            say("毅哥，今日收盘总结，" + summary.replace('\n', '，'))
            log("监控结束")
            break

if __name__ == '__main__':
    main()
