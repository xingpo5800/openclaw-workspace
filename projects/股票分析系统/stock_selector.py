#!/usr/bin/env python3
"""
5日量上穿60日均量 · 选股脚本 v2
策略条件:
  - slope > 30 (5日均量相对5日前的增长)
  - RSI < 52
  - 量比 0.85 ~ 1.05 (上穿临界)
分批策略:
  - 第一批: 取全市场前500只, slope>20 入候选池
  - 第二批: 对候选池详细计算, 命中立即打印
"""

import ssl
import time
import json
import random
import urllib.request
import urllib.error
from datetime import datetime

# SSL 修复
ssl._create_default_https_context = ssl._create_unverified_context

# ========== 配置 ==========
WORK_DIR = "/Users/kevin/.openclaw/workspace/projects/股票分析系统"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
REQUEST_DELAY = 0.05
REQUEST_TIMEOUT = 10
MAX_RETRIES = 2

# 筛选条件
SLOPE_FIRST_THRESHOLD = 20   # 第一批初筛
SLOPE_FINAL_THRESHOLD = 30   # 最终门槛
RSI_MAX = 52
VOL_RATIO_MIN = 0.85
VOL_RATIO_MAX = 1.05
FIRST_BATCH_SIZE = 500       # 第一批取500只
KLINE_MIN_DAYS = 65          # K线最少天数


# ========== 工具函数 ==========
def http_get(url, timeout=REQUEST_TIMEOUT, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep((attempt + 1) * 1.5 + random.uniform(0, 0.5))
    return None


def sleep():
    time.sleep(REQUEST_DELAY + random.uniform(0, 0.02))


# ========== 指标计算 ==========
def calculate_slope(volumes):
    """量能斜率: (当前5日均量 / 5日前的5日均量 - 1) * 100"""
    if len(volumes) < 10:
        return None
    ma5_now = sum(volumes[-5:]) / 5
    ma5_5ago = sum(volumes[-10:-5]) / 5
    if ma5_5ago == 0:
        return None
    return (ma5_now / ma5_5ago - 1) * 100


def calculate_rsi(closes, period=14):
    """RSI"""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))


def calculate_vol_ratio(volumes):
    """量比: 当前成交量 / 5日均量"""
    if len(volumes) < 6:
        return None
    ma5 = sum(volumes[-5:]) / 5
    if ma5 == 0:
        return None
    return volumes[-1] / ma5


def is_st_stock(name):
    """判断是否ST股"""
    name_upper = name.upper()
    return ("ST" in name_upper or "*ST" in name_upper or
            "S*ST" in name_upper or "*SST" in name_upper or
            "S ST" in name_upper or "SST" in name_upper)


# ========== 获取K线数据 ==========
def get_kline(secid):
    """
    获取日K线数据，返回 (closes, volumes)
    """
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}"
        f"&fields1=f1,f2,f3,f4,f5"
        f"&fields2=f51,f52,f53,f54,f55,f56"
        f"&klt=101&fqt=1"
        f"&beg=20231201"
        f"&end=20260326&lmt=70"
    )
    data = http_get(url)
    if not data or data.get("data") is None:
        return None, None

    klines = data["data"].get("klines", [])
    if len(klines) < KLINE_MIN_DAYS:
        return None, None

    closes, volumes = [], []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            closes.append(float(parts[2]))
            volumes.append(float(parts[5]))
        except (ValueError, IndexError):
            continue

    if len(closes) < KLINE_MIN_DAYS or len(volumes) < KLINE_MIN_DAYS:
        return None, None

    return closes, volumes


# ========== 获取实时行情 ==========
def get_realtime(secid):
    """获取实时行情: 现价、涨跌幅、量比"""
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/get"
        f"?secid={secid}"
        f"&fields=f43,f169,f170,f47"
    )
    data = http_get(url, timeout=5)
    if not data or data.get("data") is None:
        return None, None, None

    d = data["data"]
    price = d.get("f43", 0)
    if price and price > 10000:
        price = price / 100
    pct = d.get("f170", 0)      # 万分之一
    vol_ratio = d.get("f47", 0) # 量比
    return price, pct, vol_ratio


# ========== 获取全市场股票列表(第一批,限500只) ==========
def get_first_batch_stocks():
    """
    获取全市场股票前500只，仅包含主板A股(沪6/深0,3)，
    过滤ST股和北交所股票。
    fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23
    (沪市主板6开头 + 科创板0开头? wait:
     m:0+t:6=沪市主板, m:0+t:13=科创板,
     m:1+t:2=深市主板, m:1+t:23=创业板)
    只取 m:0+t:6 + m:1+t:2 + m:1+t:23，跳过科创板
    """
    stocks = []
    skipped_st = 0
    skipped_bj = 0
    skipped_small = 0
    page_size = 100
    page = 1
    # 只取沪市主板(6开头) + 深市主板(0开头) + 创业板(3开头)
    fs_filter = "m:0+t:6,m:1+t:2,m:1+t:23"
    total = 0
    total_known = False

    print("[1/3] 获取全市场股票列表 (限前500只)...")

    while len(stocks) < FIRST_BATCH_SIZE:
        url = (
            f"https://push2.eastmoney.com/api/qt/clist/get"
            f"?pn={page}&pz={page_size}&po=1&np=1&fltt=2&invt=2&fid=f3"
            f"&fs={fs_filter}"
            f"&fields=f2,f3,f12,f14,f100"
        )
        data = http_get(url)
        if not data or data.get("data") is None:
            print(f"  [警告] 第{page}页请求失败，停止")
            break

        if not total_known:
            total = data["data"].get("total", 0)
            print(f"  → 市场总计约 {total} 只")
            total_known = True

        diff = data["data"].get("diff", [])
        if not diff:
            break

        for s in diff:
            if len(stocks) >= FIRST_BATCH_SIZE:
                break

            name = s.get("f14", "")
            code = str(s.get("f12", ""))
            market = s.get("f100", "")  # 市场标识

            # 1. 过滤北交所: 代码8开头 或 market=bj
            if code.startswith("8") or market == "bj":
                skipped_bj += 1
                continue

            # 2. 过滤ST股
            if is_st_stock(name):
                skipped_st += 1
                continue

            # 3. 过滤退市/停牌
            price = s.get("f2", 0)
            if price == 0 or price == "-" or price == "--":
                skipped_small += 1
                continue

            # 4. 过滤科创板(代码以688开头，实际在深交所)
            #    这里只取6/0/3开头，沪主板6开头，深市0/3开头
            if not (code.startswith("6") or code.startswith("0") or code.startswith("3")):
                skipped_small += 1
                continue

            # 构造 secid
            if code.startswith("6"):
                secid = f"1.{code}"   # 沪市
            else:
                secid = f"0.{code}"   # 深市(含创业板)

            stocks.append({
                "name": name,
                "code": code,
                "secid": secid,
                "price": price,
                "pct": s.get("f3", 0),
            })

        fetched = page * page_size
        if fetched >= total:
            break
        page += 1
        sleep()

    print(f"  → 有效股票 {len(stocks)} 只 "
          f"(过滤ST {skipped_st} | 北交所 {skipped_bj} | 其他 {skipped_small})")
    return stocks


# ========== 第一批: 初筛slope>20 ==========
def first_batch_screen(stocks):
    """
    对 stocks 逐只获取K线，计算 slope>20 的加入候选池
    """
    candidates = []
    checked = 0
    total = len(stocks)

    print(f"\n[2/3] 第一批初筛: slope > {SLOPE_FIRST_THRESHOLD} ({total} 只)...")

    for i, stock in enumerate(stocks):
        checked += 1
        secid = stock["secid"]

        if checked % 100 == 0:
            print(f"  进度: {checked}/{total} ({checked*100//total}%)")

        closes, volumes = get_kline(secid)
        sleep()

        if closes is None:
            continue

        slope = calculate_slope(volumes)
        if slope is not None and slope > SLOPE_FIRST_THRESHOLD:
            candidates.append({
                "name": stock["name"],
                "code": stock["code"],
                "secid": secid,
                "price": stock["price"],
                "pct": stock["pct"],
                "slope": slope,
            })

    print(f"  → 完成初筛 {checked} 只，候选池 {len(candidates)} 只")
    return candidates


# ========== 第二批: 详细计算RSI和量比，命中立即打印 ==========
def second_batch_screen(candidates, result_file):
    """
    对候选池逐只计算 RSI + 量比，命中立即打印并写入文件
    """
    total = len(candidates)
    hits = []
    hit_count = 0

    print(f"\n[3/3] 第二批精筛: slope>{SLOPE_FINAL_THRESHOLD} & RSI<{RSI_MAX} & "
          f"量比{VOL_RATIO_MIN}~{VOL_RATIO_MAX} ({total} 只候选)...")

    for i, stock in enumerate(candidates):
        secid = stock["secid"]

        if (i + 1) % 10 == 0:
            print(f"  进度: {i+1}/{total}")

        # 重新获取K线算RSI
        closes, volumes = get_kline(secid)
        sleep()

        if closes is None:
            continue

        rsi = calculate_rsi(closes)
        vol_ratio = calculate_vol_ratio(volumes)
        slope = stock["slope"]  # 第一批已算过

        if rsi is None or vol_ratio is None:
            continue

        # 全条件判断
        if (slope <= SLOPE_FINAL_THRESHOLD or
                rsi >= RSI_MAX or
                vol_ratio < VOL_RATIO_MIN or
                vol_ratio > VOL_RATIO_MAX):
            continue

        # 获取实时行情
        price, pct, vol_ratio_rt = get_realtime(secid)
        if price is None:
            price = stock["price"]
            pct = stock["pct"]
        if vol_ratio_rt and vol_ratio_rt > 0:
            vol_ratio = vol_ratio_rt

        # 格式化涨幅
        pct_str = f"{pct/100:.2f}%" if pct else "N/A"

        hit = {
            "name": stock["name"],
            "code": stock["code"],
            "price": price,
            "pct_str": pct_str,
            "pct": pct,
            "slope": round(slope, 2),
            "rsi": round(rsi, 2),
            "vol_ratio": round(vol_ratio, 2),
        }
        hits.append(hit)
        hit_count += 1

        # 命中立即打印
        print(f"【命中】{stock['name']} {stock['code']} 现价:{price} "
              f"涨幅:{pct_str} slope:{hit['slope']} "
              f"RSI:{hit['rsi']} 量比:{hit['vol_ratio']}")

        # 立即写入文件(追加)
        try:
            with open(result_file, "a", encoding="utf-8") as f:
                f.write(f"【命中】{stock['name']} {stock['code']} "
                        f"现价:{price} 涨幅:{pct_str} "
                        f"slope:{hit['slope']} RSI:{hit['rsi']} "
                        f"量比:{hit['vol_ratio']}\n")
        except Exception as e:
            print(f"  [写入失败] {e}")

    print(f"\n  → 第二批完成，命中 {hit_count} 只")
    return hits


# ========== 主流程 ==========
def screen_stocks():
    start_time = datetime.now()

    print("=" * 65)
    print("  5日量上穿60日均量 · 选股扫描 v2")
    print(f"  扫描时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print(f"  条件: slope > {SLOPE_FINAL_THRESHOLD}, RSI < {RSI_MAX}, "
          f"量比 {VOL_RATIO_MIN}~{VOL_RATIO_MAX}")
    print(f"  数据: 主板A股(沪6/深0,3)，过滤ST/北交所")
    print("=" * 65)

    # 初始化结果文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"{WORK_DIR}/选股结果_{timestamp}.txt"
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(f"选股扫描结果 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"条件: slope>{SLOPE_FINAL_THRESHOLD}, RSI<{RSI_MAX}, "
                    f"量比{VOL_RATIO_MIN}~{VOL_RATIO_MAX}\n")
            f.write(f"过滤: ST股、北交所股票\n")
            f.write("=" * 60 + "\n\n")
    except Exception as e:
        print(f"[错误] 无法创建结果文件: {e}")
        return

    # Step 1: 获取股票列表
    stocks = get_first_batch_stocks()
    if not stocks:
        print("没有获取到股票列表，退出。")
        return

    # Step 2: 第一批初筛
    candidates = first_batch_screen(stocks)
    if not candidates:
        print("候选池为空，扫描结束。")
        with open(result_file, "a", encoding="utf-8") as f:
            f.write("\n候选池为空，无命中。\n")
        return

    # Step 3: 第二批精筛(命中立即打印)
    hits = second_batch_screen(candidates, result_file)

    # 汇总
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*65}")
    print(f"扫描完成! 用时 {elapsed:.1f}秒，命中 {len(hits)} 只")
    print(f"{'='*65}")

    if hits:
        # 按slope降序打印汇总
        hits.sort(key=lambda x: x["slope"], reverse=True)
        print(f"\n{'序':>3} {'名称':^8} {'代码':^10} {'现价':>7} {'涨幅':>8} "
              f"{'slope':>8} {'RSI':>6} {'量比':>6}")
        print("-" * 65)
        for i, h in enumerate(hits, 1):
            print(f"{i:>3} {h['name']:^8} {h['code']:^10} "
                  f"{h['price']:>7.2f} {h['pct_str']:>8} "
                  f"{h['slope']:>8.2f} {h['rsi']:>6.2f} {h['vol_ratio']:>6.2f}")

    # 写最终统计
    try:
        with open(result_file, "a", encoding="utf-8") as f:
            f.write(f"\n扫描完成! 用时 {elapsed:.1f}秒，命中 {len(hits)} 只\n")
            f.write(f"结果文件: {result_file}\n")
    except:
        pass

    print(f"\n结果已保存: {result_file}")
    return hits


# ========== 入口 ==========
if __name__ == "__main__":
    screen_stocks()
