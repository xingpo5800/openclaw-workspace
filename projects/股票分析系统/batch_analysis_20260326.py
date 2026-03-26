# -*- coding: utf-8 -*-
"""
批量股票缠论+量价综合分析 v20260326
"""
import requests
import json
import math
import time
from datetime import datetime, timedelta

# 导入本地缠论核心算法
import sys
sys.path.insert(0, '/Users/kevin/.openclaw/workspace/projects/股票分析系统')
from chan_core import (
    resolve_inclusion, find_fenxing, identify_bi, identify_seg,
    find_zhongshu, calc_macd_for_bis, find_beichi, find_maidian
)

# ========== 股票池 ==========
STOCKS = [
    ('601899', '紫金矿业', 33.01, -0.69),
    ('002202', '金风科技', 28.25, -0.21),
    ('002487', '大金重工', 75.23, +2.72),
    ('605117', '德业股份', 130.34, -0.12),
    ('600367', '红星发展', 22.26, -1.15),
    ('002929', '润建股份', 49.96, -1.17),
    ('300830', '金现代', 10.93, -0.64),
    ('002506', '协鑫集成', 5.56, -3.97),
    ('688195', '腾景科技', 272.96, -2.16),
    ('300389', '艾比森', 20.57, +0.24),
    ('000809', '和展能源', 4.26, +4.93),
]

# ========== 东方财富K线接口 ==========
def fetch_kline_eastmoney(secid, days=120):
    """从东方财富获取日K线数据"""
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",  # 日K
        "fqt": "1",    # 前复权
        "end": "20500101",
        "lmt": days,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get('data') and data['data'].get('klines'):
            lines = data['data']['klines']
            klines = []
            for line in lines:
                parts = line.split(',')
                klines.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': float(parts[5]) if len(parts) > 5 else 0,
                })
            return klines
    except Exception as e:
        print(f"  数据获取失败: {e}")
    return []


def get_secid(code):
    """根据股票代码返回东方财富secid"""
    if code.startswith('6'):
        return f"1.{code}"
    else:
        return f"0.{code}"


# ========== 量价分析 ==========
def volume_price_analysis(klines):
    """量价综合分析"""
    if len(klines) < 60:
        return {}

    closes = [k['close'] for k in klines]
    volumes = [k['volume'] for k in klines]

    # 均线
    def ma(data, n):
        if len(data) < n:
            return None
        return sum(data[-n:]) / n

    ma5_vol = ma(volumes, 5)
    ma20_vol = ma(volumes, 20)
    ma60_vol = ma(volumes, 60)
    ma5_price = ma(closes, 5)
    ma20_price = ma(closes, 20)
    ma60_price = ma(closes, 60)

    # 量能斜率（最近20日量能回归）
    def volume_slope(vols, n=20):
        if len(vols) < n:
            return 0
        recent = vols[-n:]
        # 简单线性斜率
        x = list(range(n))
        y = recent
        x_mean = (n - 1) / 2
        y_mean = sum(y) / n
        num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        den = sum((x[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        return slope

    vol_slope = volume_slope(volumes, 20)
    vol_slope_norm = vol_slope / (ma60_vol * 0.1) if ma60_vol else 0  # 归一化

    # 今日量能相对均量
    today_vol = volumes[-1]
    vol_ratio_5 = today_vol / ma5_vol if ma5_vol else 0
    vol_ratio_60 = today_vol / ma60_vol if ma60_vol else 0

    # 近期涨跌
    recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0

    # 创N日新高/新低
    high20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
    low20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
    is_high20 = closes[-1] >= high20 * 0.98
    is_low20 = closes[-1] <= low20 * 1.02

    return {
        'ma5_vol': round(ma5_vol, 0) if ma5_vol else 0,
        'ma20_vol': round(ma20_vol, 0) if ma20_vol else 0,
        'ma60_vol': round(ma60_vol, 0) if ma60_vol else 0,
        'ma5_price': round(ma5_price, 2) if ma5_price else 0,
        'ma20_price': round(ma20_price, 2) if ma20_price else 0,
        'ma60_price': round(ma60_price, 2) if ma60_price else 0,
        'vol_slope': round(vol_slope, 0),
        'vol_slope_norm': round(vol_slope_norm, 3),
        'vol_ratio_5': round(vol_ratio_5, 2),
        'vol_ratio_60': round(vol_ratio_60, 2),
        'recent_change': round(recent_change, 2),
        'is_high20': is_high20,
        'is_low20': is_low20,
    }


# ========== 缠论评分 ==========
def chan_score(bis, zhongshu_list, beichi_signals, maidian, last_price):
    """缠论维度评分（满分10）"""
    score = 0
    details = []

    if not bis or len(bis) < 3:
        return 0, "笔不足", []

    # 当前趋势方向（最近一笔）
    last_bi = bis[-1]
    trend = last_bi['type']

    # 中枢数量
    z_count = len(zhongshu_list)
    score += min(z_count, 3) * 0.5
    details.append(f"中枢数:{z_count}")

    # 背驰信号
    bc_count = len(beichi_signals)
    score += min(bc_count, 2) * 1.0
    details.append(f"背驰信号:{bc_count}")

    # 买卖点
    buys = [m for m in maidian['buy'] if m['strength'] >= 1.0]
    sells = [m for m in maidian['sell'] if m['strength'] >= 1.0]
    score += min(len(buys), 2) * 1.5
    details.append(f"买点:{len(buys)}")

    # 当前位置与中枢关系
    for z in zhongshu_list[-1:]:
        if trend == 'up':
            dist_from_zd = (last_price - z['zd']) / z['zd'] * 100
            if last_price > z['zg']:
                score += 2  # 离开中枢上方，强
                details.append(f"价格({last_price:.2f})>ZG({z['zg']:.2f})，离开中枢")
            elif last_price > z['zd']:
                score += 1
                details.append(f"价格在中枢内")
        else:
            dist_from_zg = (z['zg'] - last_price) / z['zg'] * 100
            if last_price < z['zd']:
                score += 2
                details.append(f"价格({last_price:.2f})<ZD({z['zd']:.2f})，离开中枢")
            elif last_price < z['zg']:
                score += 1

    # 趋势稳定性（笔幅度一致性）
    if len(bis) >= 4:
        recent_amps = [abs(b['amplitude']) for b in bis[-4:]]
        amp_std = math.sqrt(sum((x - sum(recent_amps)/4)**2 for x in recent_amps) / 4)
        amp_mean = sum(recent_amps) / 4
        cv = amp_std / amp_mean if amp_mean > 0 else 1
        if cv < 0.5:
            score += 1
            details.append(f"趋势稳定(CV={cv:.2f})")

    score = min(score, 10)
    return round(score, 1), "; ".join(details), buys


# ========== 蜡烛图评分 ==========
def candle_score(klines):
    """蜡烛图评分（满分10）"""
    if len(klines) < 10:
        return 0, "数据不足"

    recent = klines[-10:]

    # 基础结构
    up_count = sum(1 for k in recent if k['close'] > k['open'])
    down_count = 10 - up_count

    # 近期形态
    last = recent[-1]
    prev = recent[-2]

    body = abs(last['close'] - last['open'])
    full_range = last['high'] - last['low']
    upper_shadow = last['high'] - max(last['open'], last['close'])
    lower_shadow = min(last['open'], last['close']) - last['low']

    score = 5
    details = []

    # 阳线/阴线
    if last['close'] > last['open']:
        score += 0.5
        details.append("收阳")
    else:
        score -= 0.5
        details.append("收阴")

    # 实体比例（实体大更好）
    if full_range > 0:
        body_ratio = body / full_range
        if body_ratio > 0.7:
            score += 1
            details.append(f"实体强({body_ratio:.0%})")
        elif body_ratio < 0.3:
            score -= 1
            details.append(f"十字星/锤({body_ratio:.0%})")

    # 下影线（底分型特征）
    if lower_shadow > body * 1.5 and lower_shadow > upper_shadow:
        score += 1.5
        details.append("长下影(支撑强)")
    elif upper_shadow > body * 1.5 and upper_shadow > lower_shadow:
        score -= 1.0
        details.append("长上影(压力强)")

    # 连续阳线
    consecutive_up = 0
    for k in reversed(recent):
        if k['close'] > k['open']:
            consecutive_up += 1
        else:
            break
    if consecutive_up >= 3:
        score += 1.5
        details.append(f"连阳{consecutive_up}天")
    elif consecutive_up == 0 and consecutive_up == 0:
        score -= 0.5

    # 突破20日高点
    high20 = max(k['high'] for k in recent)
    if last['close'] >= high20 * 0.98:
        score += 1
        details.append("接近20日高点")
    low20 = min(k['low'] for k in recent)
    if last['close'] <= low20 * 1.02:
        score -= 1
        details.append("接近20日低点")

    # 均线多头/空头
    closes = [k['close'] for k in klines]
    if len(closes) >= 20:
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        if ma5 > ma20:
            score += 0.5
            details.append("MA5>MA20多头")
        else:
            score -= 0.5
            details.append("MA5<MA20空头")

    score = max(0, min(score, 10))
    return round(score, 1), "; ".join(details)


# ========== 量价评分 ==========
def vol_score(vp_data, current_change):
    """量价维度评分（满分10）"""
    score = 5
    details = []

    if not vp_data:
        return 0, "数据不足"

    # 量能放大（相对5日均量）
    vr5 = vp_data.get('vol_ratio_5', 1)
    if vr5 >= 2.0:
        score += 2
        details.append(f"量能爆量({vr5:.1f}x)")
    elif vr5 >= 1.5:
        score += 1
        details.append(f"量能放大({vr5:.1f}x)")
    elif vr5 < 0.5:
        score -= 1
        details.append("量能萎缩")

    # 量能趋势（斜率）
    slope = vp_data.get('vol_slope_norm', 0)
    if slope > 0.2:
        score += 1
        details.append("量能上升趋势")
    elif slope < -0.2:
        score -= 1
        details.append("量能下降趋势")

    # 60日均量对比（判断相对位置）
    vr60 = vp_data.get('vol_ratio_60', 1)
    if vr60 >= 1.5:
        score += 1
        details.append("量能高于60日均量")
    elif vr60 < 0.7:
        score -= 0.5
        details.append("量能低于60日均量")

    # 涨跌配合（涨时放量/跌时缩量）
    if current_change > 0 and vr5 >= 1.2:
        score += 1.5
        details.append("价涨量增(健康)")
    elif current_change > 0 and vr5 < 0.8:
        score -= 1
        details.append("价涨量缩(背离)")
    elif current_change < 0 and vr5 >= 1.5:
        score -= 0.5
        details.append("价跌量增(不健康)")
    elif current_change < 0 and vr5 < 0.8:
        score += 1
        details.append("价跌量缩(健康)")

    # 均线多头排列
    ma5p = vp_data.get('ma5_price', 0)
    ma20p = vp_data.get('ma20_price', 0)
    ma60p = vp_data.get('ma60_price', 0)
    if ma5p > ma20p > ma60p > 0:
        score += 1
        details.append("均线多头")
    elif ma5p < ma20p < ma60p:
        score -= 1
        details.append("均线空头")

    score = max(0, min(score, 10))
    return round(score, 1), "; ".join(details)


# ========== 真技术评分 ==========
def true_tech_score(klines, current_price, current_change):
    """真技术评分（满分10）—— 综合动能/结构/位置"""
    if len(klines) < 60:
        return 0, "数据不足", {}

    closes = [k['close'] for k in klines]

    # === 动量指标 ===
    def ema(data, n):
        k = 2 / (n + 1)
        result = [data[0]]
        for d in data[1:]:
            result.append(d * k + result[-1] * (1 - k))
        return result

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    dif = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = ema(dif, 9)
    macd = [2 * (dif[i] - dea[i]) for i in range(len(dif))]

    # MACD柱当前值
    macd_now = macd[-1] if macd else 0
    macd_prev = macd[-2] if len(macd) > 1 else 0
    macd_sum_5 = sum(macd[-5:])

    # === RSI ===
    def calc_rsi(data, n=14):
        deltas = [data[i] - data[i-1] for i in range(1, len(data))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        if len(gains) < n:
            return 50
        avg_gain = sum(gains[-n:]) / n
        avg_loss = sum(losses[-n:]) / n
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    rsi14 = calc_rsi(closes, 14)
    rsi6 = calc_rsi(closes, 6)

    # === KDJ ===
    def calc_kdj(klines_data, n=9):
        lows = [k['low'] for k in klines_data]
        highs = [k['high'] for k in klines_data]
        k_vals = [50]
        d_vals = [50]
        for i in range(n, len(lows)):
            rsv = (closes[i] - min(lows[i-n:i+1])) / (max(highs[i-n:i+1]) - min(lows[i-n:i+1]) + 0.001) * 100
            k = k_vals[-1] * 2/3 + rsv * 1/3
            d = d_vals[-1] * 2/3 + k * 1/3
            k_vals.append(k)
            d_vals.append(d)
        if len(k_vals) < 3:
            return 50, 50, 0
        j = 3 * k_vals[-1] - 2 * d_vals[-1]
        return k_vals[-1], d_vals[-1], j

    k_val, d_val, j_val = calc_kdj(klines[-30:])

    score = 5
    details = []
    signals = {}

    # MACD
    if macd_now > 0 and macd_prev <= 0:
        score += 1.5
        details.append("MACD金叉")
        signals['macd_cross'] = 'golden'
    elif macd_now < 0 and macd_prev >= 0:
        score -= 1.5
        details.append("MACD死叉")
        signals['macd_cross'] = 'dead'
    elif macd_now > 0:
        score += 0.5
        details.append("MACD红柱")

    # MACD收敛/发散（价格vs MACD背离）
    if len(closes) >= 10:
        price_trend = (closes[-1] - closes[-10]) / closes[-10] * 100
        macd_trend = (macd_now - macd[-10]) / (abs(macd[-10]) + 0.001) * 100
        if price_trend > 0 and macd_trend < -10:
            score += 1.5
            details.append("MACD顶背离(看跌)")
        elif price_trend < 0 and macd_trend > 10:
            score += 1.5
            details.append("MACD底背离(看涨)")

    # RSI
    if rsi14 > 70:
        score -= 1
        details.append(f"RSI超买({rsi14:.0f})")
    elif rsi14 < 30:
        score += 1
        details.append(f"RSI超卖({rsi14:.0f})")
    elif 40 <= rsi14 <= 60:
        score += 0.5
        details.append(f"RSI中性({rsi14:.0f})")

    if rsi6 > rsi14 and rsi6 < 70:
        score += 0.5
        details.append("RSI短线强势")

    # KDJ
    if k_val > d_val and k_val < 80:
        score += 0.5
        details.append("KDJ金叉")
    elif k_val < d_val and k_val > 20:
        score -= 0.5
        details.append("KDJ死叉")

    if j_val < 20:
        score += 1
        details.append(f"KDJ超卖(J={j_val:.0f})")
    elif j_val > 100:
        score -= 1
        details.append(f"KDJ超买(J={j_val:.0f})")

    # 布林带
    bb_period = 20
    if len(closes) >= bb_period:
        ma_b = sum(closes[-bb_period:]) / bb_period
        std = math.sqrt(sum((c - ma_b) ** 2 for c in closes[-bb_period:]) / bb_period)
        upper = ma_b + 2 * std
        lower = ma_b - 2 * std
        bb_width = (upper - lower) / ma_b * 100

        if current_price <= lower * 1.02:
            score += 1.5
            details.append("触及布林下轨(超卖)")
        elif current_price >= upper * 0.98:
            score -= 1.5
            details.append("触及布林上轨(超买)")
        elif current_price > ma_b:
            score += 0.5
            details.append("价格>布林中轨")

    # 当前位置评分
    if len(closes) >= 60:
        ma60 = sum(closes[-60:]) / 60
        if current_price > ma60:
            score += 0.5
            details.append("价格>60日均线")
        else:
            score -= 0.5

    score = max(0, min(score, 10))
    return round(score, 1), "; ".join(details), {
        'macd': round(macd_now, 4),
        'rsi14': round(rsi14, 1),
        'rsi6': round(rsi6, 1),
        'kdj_k': round(k_val, 1),
        'kdj_d': round(d_val, 1),
        'kdj_j': round(j_val, 1),
        'macd_5sum': round(macd_sum_5, 4),
    }


# ========== 主分析流程 ==========
def analyze_stock(code, name, current_price, current_change):
    """对单只股票进行完整分析"""
    print(f"\n{'='*60}")
    print(f"📊 分析: {code} {name} | 现价: {current_price} | 涨幅: {current_change:+.2f}%")
    print(f"{'='*60}")

    secid = get_secid(code)
    klines = fetch_kline_eastmoney(secid, days=150)

    if not klines or len(klines) < 60:
        print(f"  ⚠️ 数据不足，跳过")
        return None

    print(f"  获取到 {len(klines)} 根日K线")

    # === 缠论分析 ===
    resolved = resolve_inclusion(klines)
    bis = identify_bi(resolved, min_bars=5)
    zhongshu_list = find_zhongshu(bis)
    macd_data = calc_macd_for_bis(resolved, bis)
    beichi_signals = find_beichi(bis, zhongshu_list, macd_data)
    maidian = find_maidian(bis, zhongshu_list, beichi_signals)

    # === 量价分析 ===
    vp = volume_price_analysis(klines)

    # === 四维打分 ===
    chan_s, chan_d, buys = chan_score(bis, zhongshu_list, beichi_signals, maidian, current_price)
    candle_s = candle_score(klines)[0]
    vol_s = vol_score(vp, current_change)
    true_s, true_d, tech_ind = true_tech_score(klines, current_price, current_change)

    total = chan_s + candle_s + vol_s + true_s

    print(f"\n  🏆 四维评分:")
    print(f"    缠论: {chan_s}/10 | 蜡烛: {candle_s}/10 | 量价: {vol_s}/10 | 真技术: {true_s}/10")
    print(f"    综合: {total}/40")
    print(f"  缠论: {chan_d}")
    print(f"  量价: vol_ratio_5={vp.get('vol_ratio_5',0):.2f}, vol_ratio_60={vp.get('vol_ratio_60',0):.2f}")
    print(f"  真技术: {true_d}")
    print(f"  技术指标: MACD={tech_ind.get('macd',0):.4f}, RSI6={tech_ind.get('rsi6',0):.1f}, RSI14={tech_ind.get('rsi14',0):.1f}, J={tech_ind.get('kdj_j',0):.1f}")

    # 笔和背驰摘要
    print(f"  笔数量: {len(bis)}, 中枢数: {len(zhongshu_list)}, 背驰: {len(beichi_signals)}")
    if bis:
        print(f"  最近3笔: {[(b['type'], b['start_date'][:8], b['end_date'][:8]) for b in bis[-3:]]}")
    if zhongshu_list:
        z = zhongshu_list[-1]
        print(f"  最近中枢: ZG={z['zg']:.2f}, ZD={z['zd']:.2f}, GG={z.get('gg',0):.2f}, DD={z.get('dd',0):.2f}")

    # 买点列表
    if buys:
        print(f"  📍 买点信号: {[(b['name'], b['date'][:8], f"¥{b['price']:.2f}") for b in buys[:3]]}")

    return {
        'code': code, 'name': name,
        'current_price': current_price, 'current_change': current_change,
        'klines_count': len(klines),
        'bis_count': len(bis), 'zhongshu_count': len(zhongshu_list),
        'beichi_count': len(beichi_signals),
        'scores': {'chan': chan_s, 'candle': candle_s, 'vol': vol_s, 'true': true_s, 'total': total},
        'chan_detail': chan_d,
        'vp_data': vp,
        'true_tech_detail': true_d,
        'tech_indicators': tech_ind,
        'buys': buys[:3],
        'sells': maidian['sell'][:3],
        'last_bi': bis[-1] if bis else None,
        'last_zs': zhongshu_list[-1] if zhongshu_list else None,
        'beichi_signals': beichi_signals[:3],
    }


# ========== 生成报告 ==========
def generate_report(results):
    """生成Markdown分析报告"""
    today = datetime.now().strftime('%Y-%m-%d')

    # 筛选有机会的票：总分>=20 且有明确买点
    opportunity = [r for r in results if r and r['scores']['total'] >= 20 and r['buys']]
    opportunity.sort(key=lambda x: x['scores']['total'], reverse=True)

    all_results = [r for r in results if r]
    all_results.sort(key=lambda x: x['scores']['total'], reverse=True)

    md = f"""# 📈 股票批量综合分析报告

> **分析日期**: {today}  
> **股票池**: {len(STOCKS)} 只  
> **方法**: 缠论(笔/中枢/背驰/买卖点) + 量价(均量/斜率) + 四维打分  
> **数据来源**: 东方财富日K线

---

## 一、评分总览（全部 {len(all_results)} 只）

| 股票 | 代码 | 现价 | 涨幅 | 缠论 | 蜡烛 | 量价 | 真技术 | **总分** | 机会 |
|------|------|------|------|------|------|------|--------|----------|------|
"""

    for r in all_results:
        flag = "⭐" if r['scores']['total'] >= 20 and r['buys'] else ""
        md += f"| {r['name']} | {r['code']} | {r['current_price']} | {r['current_change']:+.2f}% | "
        md += f"{r['scores']['chan']} | {r['scores']['candle']} | {r['scores']['vol']} | "
        md += f"{r['scores']['true']} | **{r['scores']['total']}** | {flag} |\n"

    # === 有机会的票详细分析 ===
    md += f"""
---

## 二、⭐ 机会清单（共 {len(opportunity)} 只，总分≥20 且有明确买点）

"""
    if not opportunity:
        md += "> 暂无符合条件的票，建议等待更好的入场时机。\n"
    else:
        for i, r in enumerate(opportunity, 1):
            change = r['current_change']
            trend_desc = "强势上涨" if change > 2 else "小幅上涨" if change > 0 else "回调" if change > -2 else "大幅回调"

            md += f"""
### {i}. {r['name']}（{r['code']}）⭐

**基本行情**: 现价 ¥{r['current_price']} | 今日 {change:+.2f}% | {trend_desc}

**四维评分**: 缠论 {r['scores']['chan']}/10 + 蜡烛 {r['scores']['candle']}/10 + 量价 {r['scores']['vol']}/10 + 真技术 {r['scores']['true']}/10 = **{r['scores']['total']}/40**

**缠论状态**:
- 笔数量: {r['bis_count']} | 中枢数: {r['zhongshu_count']} | 背驰信号: {r['beichi_count']}
- {r['chan_detail']}

"""
            if r['last_zs']:
                z = r['last_zs']
                md += f"**最近中枢**: ZG={z['zg']:.2f} / ZD={z['zd']:.2f}（振幅{z['range_width']:.2f}%）\n\n"

            md += "**买点信号**:\n"
            for b in r['buys']:
                md += f"- {b['name']} | 日期:{b['date'][:8]} | 价格:¥{b['price']:.2f} | 强度:{b['strength']}\n"

            md += "\n**量价数据**:\n"
            vp = r['vp_data']
            md += f"- 5日均量: {vp.get('ma5_vol',0):,.0f} | 20日均量: {vp.get('ma20_vol',0):,.0f} | 60日均量: {vp.get('ma60_vol',0):,.0f}\n"
            md += f"- 今日量/5日均量: {vp.get('vol_ratio_5',0):.2f}x | 今日量/60日均量: {vp.get('vol_ratio_60',0):.2f}x\n"
            md += f"- 量能斜率: {vp.get('vol_slope_norm',0):+.3f}（>0为上升趋势）\n"

            ti = r['tech_indicators']
            md += "\n**技术指标**:\n"
            md += f"- MACD: {ti.get('macd',0):.4f} | RSI6: {ti.get('rsi6',0):.1f} | RSI14: {ti.get('rsi14',0):.1f}\n"
            md += f"- KDJ: K={ti.get('kdj_k',0):.1f} D={ti.get('kdj_d',0):.1f} J={ti.get('kdj_j',0):.1f}\n"

            md += f"\n**真技术评价**: {r['true_tech_detail']}\n"

            # === 具体介入建议 ===
            md += "\n**📍 介入建议**:\n"
            buy_price = r['current_price']
            last_bi = r['last_bi']
            last_zs = r['last_zs']

            if r['buys']:
                best_buy = r['buys'][0]
                ideal_buy_price = best_buy['price']

                if change > 0:
                    # 今日已涨，等待回调
                    # 回调到5日线或10日线附近介入
                    ma5p = vp.get('ma5_price', buy_price * 0.98)
                    ma10_est = buy_price * 0.99  # 估算
                    md += f"- ⚠️ 今日已涨 {change:+.2f}%，**不宜追高**\n"
                    md += f"- 建议等回调至 **¥{ma5p:.2f}** 附近（5日均线支撑）再买\n"
                    md += f"- 若错过5日线，等回调至 **¥{ideal_buy_price:.2f}**（历史买点区间）\n"
                    md += f"- **止损**: 设在 ¥{ma5p * 0.97:.2f}（跌破5日线止损，-3%空间）\n"
                    md += f"- **目标**: 第一目标 ¥{buy_price * 1.05:.2f}（+5%），第二目标 ¥{buy_price * 1.10:.2f}（+10%）\n"
                else:
                    # 今日下跌或震荡，可能有机会
                    if abs(change) < 1:
                        md += f"- 今日小幅震荡，可考虑分批建仓\n"
                    else:
                        md += f"- 今日回调 {change:.2f}%，若缩量可能是好机会\n"

                    if vp.get('vol_ratio_5', 1) < 1.0:
                        md += f"- 量能萎缩，暂时观望，等放量阳线确认\n"
                    else:
                        md += f"- 量能尚可，可考虑轻仓介入\n"

                    md += f"- **一买机会**: 参考价 ¥{ideal_buy_price:.2f}（缠论一买位置）\n"
                    md += f"- **二买机会**: 参考价 ¥{ideal_buy_price * 1.02:.2f}（回调不破一买+2%）\n"
                    md += f"- **止损**: 设在 ¥{ideal_buy_price * 0.97:.2f}（-3%止损）\n"
                    md += f"- **仓位**: 建议2-3成仓，不超过5成\n"

            md += "\n---\n"

    # ===