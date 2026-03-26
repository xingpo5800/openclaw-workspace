#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫金矿业(601899) 四维深度分析
缠论 + 蜡烛图 + 量价 + 综合评分
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chan_core import (
    resolve_inclusion, find_fenxing, identify_bi, identify_seg,
    find_zhongshu, calc_macd_for_bis, find_beichi, find_maidian,
    calc_ema as _calc_ema
)

# ===== 数据获取 =====
def get_kline_sina(code, scale, datalen=500):
    """
    新浪财经 K线 API
    scale: 5=5分钟, 15=15分钟, 30=30分钟, 240=日线
    """
    symbol = f"sh{code}" if code.startswith(('6', '5', '9')) else f"sz{code}"
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    params = {'symbol': symbol, 'scale': str(scale), 'ma': 'no', 'datalen': datalen}
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if not isinstance(data, list):
            return []
        result = []
        for bar in data:
            try:
                result.append({
                    'date': bar['day'],
                    'open': float(bar['open']),
                    'close': float(bar['close']),
                    'high': float(bar['high']),
                    'low': float(bar['low']),
                    'volume': int(float(bar.get('volume', 0)))
                })
            except:
                continue
        result.sort(key=lambda x: x['date'])
        return result
    except Exception as e:
        print(f"  获取{scale}分钟K线失败: {e}")
        return []


def get_kline_ifzq(code, scale, datalen=500):
    """腾讯 ifzq 降级接口"""
    market = 'sh' if code.startswith(('6', '5', '9')) else 'sz'
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    scale_map = {5: '5min', 15: '15min', 30: '30min', 240: 'day'}
    param_type = scale_map.get(scale, 'day')
    params = {'_var': f'kline_{param_type}hfq', 'param': f"{market}{code},{param_type},,,{datalen},qfq"}
    try:
        r = requests.get(url, params=params, timeout=10)
        text = r.text
        if '=' not in text:
            return []
        json_str = text[text.index('=') + 1:]
        data = json.loads(json_str)
        d = data.get('data', {})
        if isinstance(d, list):
            return []
        key = f"{market}{code}"
        raw = d.get(key, {}).get(param_type, d.get(key, {}).get(f"{param_type}hfq", []))
        result = []
        for line in raw:
            if len(line) >= 6:
                try:
                    result.append({
                        'date': str(line[0]), 'open': float(line[1]), 'close': float(line[2]),
                        'high': float(line[3]), 'low': float(line[4]), 'volume': int(float(line[5]))
                    })
                except:
                    continue
        result.sort(key=lambda x: x['date'])
        return result
    except:
        return []


def fetch_kline(code, scale, datalen=500):
    """双保险获取K线"""
    klines = get_kline_sina(code, scale, datalen)
    if len(klines) < 20:
        klines = get_kline_ifzq(code, scale, datalen)
    return klines


# ===== 蜡烛图分析 =====
def analyze_candlestick(klines):
    """蜡烛图形态分析"""
    if len(klines) < 5:
        return {'patterns': [], 'signal': 'neutral', 'signal_desc': '数据不足'}
    
    recent = klines[-20:] if len(klines) >= 20 else klines
    patterns = []
    signal = 'neutral'
    signal_desc = ''
    
    last5 = recent[-5:]
    last3 = recent[-3:]
    last1 = recent[-1]
    
    # === 单根K线分析 ===
    body = last1['close'] - last1['open']
    body_size = abs(body)
    range_size = last1['high'] - last1['low']
    upper_shadow = last1['high'] - max(last1['open'], last1['close'])
    lower_shadow = min(last1['open'], last1['close']) - last1['low']
    
    is_bullish = body > 0
    is_doji = body_size < range_size * 0.1
    
    # === 三根K线形态 ===
    def three_bar_pattern(bars):
        if len(bars) < 3:
            return None
        b1, b2, b3 = bars[-3], bars[-2], bars[-1]
        # 早晨之星
        if b1['close'] < b1['open'] and abs(b2['close'] - b2['open']) < (b2['high'] - b2['low']) * 0.3 and b3['close'] > b3['open']:
            if (b1['close'] - b1['open']) > abs(b2['high'] - b2['low']) * 0.5:
                return '早晨之星(底反)'
        # 黄昏之星
        if b1['close'] > b1['open'] and abs(b2['close'] - b2['open']) < (b2['high'] - b2['low']) * 0.3 and b3['close'] < b3['open']:
            if (b1['open'] - b1['close']) > abs(b2['high'] - b2['low']) * 0.5:
                return '黄昏之星(顶反)'
        # 三乌鸦（连续3天下跌）
        if all(b['close'] < b['open'] for b in bars[-3:]) and len(bars) >= 3:
            closes = [b['close'] for b in bars[-3:]]
            if closes[2] < closes[1] < closes[0]:
                return '三乌鸦(顶反)'
        # 三白兵（连续3天上涨）
        if all(b['close'] > b['open'] for b in bars[-3:]) and len(bars) >= 3:
            closes = [b['close'] for b in bars[-3:]]
            if closes[2] > closes[1] > closes[0]:
                return '三白兵(底反)'
        # 吞没形态
        if len(bars) >= 2:
            prev, curr = bars[-2], bars[-1]
            if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                if curr['open'] < prev['low'] and curr['close'] > prev['high']:
                    return '看涨吞没(底反)'
            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                if curr['open'] > prev['high'] and curr['close'] < prev['low']:
                    return '看跌吞没(顶反)'
        return None
    
    # === 近期高低点分析 ===
    def check_support_resistance(bars):
        if len(bars) < 10:
            return None
        highs = [bars[i] for i in range(5, len(bars)-1) if bars[i]['high'] > bars[i-1]['high'] and bars[i]['high'] > bars[i+1]['high']]
        lows = [bars[i] for i in range(5, len(bars)-1) if bars[i]['low'] < bars[i-1]['low'] and bars[i]['low'] < bars[i+1]['low']]
        if not highs or not lows:
            return None
        last_close = bars[-1]['close']
        nearest_resistance = min(highs[-3:], key=lambda x: abs(x['high'] - last_close))
        nearest_support = min(lows[-3:], key=lambda x: abs(x['low'] - last_close))
        return nearest_support, nearest_resistance
    
    pattern = three_bar_pattern(recent)
    if pattern:
        patterns.append(pattern)
        if '底反' in pattern or '看涨' in pattern:
            signal = 'bullish'
            signal_desc = pattern
        elif '顶反' in pattern or '看跌' in pattern:
            signal = 'bearish'
            signal_desc = pattern
    
    # === 锤子线/射击之星 ===
    if body_size > 0:
        if lower_shadow > body_size * 2 and upper_shadow < body_size * 0.3:
            patterns.append('锤子线(底反)')
            if signal != 'bearish':
                signal = 'bullish'
                signal_desc = '锤子线(底反)'
        elif upper_shadow > body_size * 2 and lower_shadow < body_size * 0.3:
            patterns.append('射击之星(顶反)')
            if signal != 'bullish':
                signal = 'bearish'
                signal_desc = '射击之星(顶反)'
    
    # === 均线支撑/压力 ===
    if len(klines) >= 5:
        ma5 = sum(k['close'] for k in klines[-5:]) / 5
        if abs(last1['close'] - ma5) / ma5 < 0.005:
            patterns.append(f'贴近5日均线({ma5:.2f})')
    
    if len(klines) >= 60:
        ma60 = sum(k['close'] for k in klines[-60:]) / 60
        if abs(last1['close'] - ma60) / ma60 < 0.01:
            patterns.append(f'贴近60日均线({ma60:.2f})')
    
    # === 连续性判断 ===
    if len(recent) >= 5:
        consecutive_up = 0
        for i in range(len(recent)-1, -1, -1):
            if recent[i]['close'] > recent[i]['open']:
                consecutive_up += 1
            else:
                break
        consecutive_down = 0
        for i in range(len(recent)-1, -1, -1):
            if recent[i]['close'] < recent[i]['open']:
                consecutive_down += 1
            else:
                break
        if consecutive_up >= 3:
            patterns.append(f'连续{consecutive_up}天上涨')
        elif consecutive_down >= 3:
            patterns.append(f'连续{consecutive_down}天下跌')
    
    if not patterns:
        patterns.append('无明显形态')
        signal_desc = '整理形态'
    
    return {
        'patterns': patterns,
        'signal': signal,
        'signal_desc': signal_desc,
        'last_bar': {
            'date': last1['date'],
            'open': last1['open'],
            'close': last1['close'],
            'high': last1['high'],
            'low': last1['low'],
            'body': round(body, 3),
            'body_pct': round(abs(body) / last1['open'] * 100, 2) if last1['open'] > 0 else 0
        }
    }


# ===== 量价分析 =====
def analyze_volume_price(klines):
    """量价综合分析"""
    if len(klines) < 5:
        return {'signal': 'neutral', 'score': 0, 'details': {}}
    
    closes = [k['close'] for k in klines]
    volumes = [k['volume'] for k in klines]
    latest_close = closes[-1]
    latest_vol = volumes[-1]
    
    # 5日均量
    vol_ma5 = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else sum(volumes) / len(volumes)
    # 10日均量
    vol_ma10 = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else vol_ma5
    # 20日均量(类60日)
    vol_ma20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else vol_ma10
    
    # 量能斜率(近5天 vs 前5天)
    if len(volumes) >= 10:
        recent5_vol = sum(volumes[-5:])
        prev5_vol = sum(volumes[-10:-5])
        vol_slope = (recent5_vol - prev5_vol) / prev5_vol * 100 if prev5_vol > 0 else 0
    else:
        vol_slope = 0
    
    # 价格斜率
    if len(closes) >= 10:
        price_slope = (closes[-1] - closes[-10]) / closes[-10] * 100
    elif len(closes) >= 5:
        price_slope = (closes[-1] - closes[-5]) / closes[-5] * 100
    else:
        price_slope = 0
    
    # 量价配合判断
    vol_ratio = latest_vol / vol_ma5 if vol_ma5 > 0 else 1
    vol_vs_60 = latest_vol / vol_ma20 if vol_ma20 > 0 else 1
    
    score = 0
    details = {}
    signal = 'neutral'
    
    # 量价齐升
    if price_slope > 1 and vol_slope > 5 and vol_ratio > 1.2:
        score = 10; signal = 'bullish'
        details['判断'] = '量价齐升，强势'
    elif price_slope > 0.5 and vol_slope > 0:
        score = 8; signal = 'bullish'
        details['判断'] = '价升量稳，良好'
    elif price_slope > 0 and vol_slope > 10:
        score = 9; signal = 'bullish'
        details['判断'] = '放量上涨，活跃'
    # 缩量整理
    elif abs(price_slope) < 1 and vol_slope < -10:
        score = 6; signal = 'neutral'
        details['判断'] = '缩量整理，观望'
    # 价跌量缩
    elif price_slope < -1 and vol_slope < 0:
        score = 4; signal = 'bearish'
        details['判断'] = '价跌量缩，偏弱'
    # 价跌量增（背离）
    elif price_slope < -1 and vol_slope > 10:
        score = 3; signal = 'bearish'
        details['判断'] = '放量下跌，警惕'
    elif price_slope < -3:
        score = 2; signal = 'bearish'
        details['判断'] = '快速下跌，弱势'
    else:
        score = 5; signal = 'neutral'
        details['判断'] = '中性整理'
    
    details['5日均量'] = f'{vol_ma5:,.0f}'
    details['20日均量'] = f'{vol_ma20:,.0f}'
    details['量能斜率'] = f'{vol_slope:.1f}%'
    details['价格斜率'] = f'{price_slope:.2f}%'
    details['量比'] = f'{vol_ratio:.2f}x'
    details['近20量比'] = f'{vol_vs_60:.2f}x'
    
    return {
        'signal': signal, 'score': score,
        'details': details,
        'vol_ma5': vol_ma5, 'vol_ma20': vol_ma20,
        'vol_slope': vol_slope, 'price_slope': price_slope,
        'vol_ratio': vol_ratio
    }


# ===== 缠论评分 =====
def chan_score(bis, zhongshu_list, beichi_signals, maidian, resolved_klines):
    """缠论评分（满分10）"""
    if not resolved_klines or len(resolved_klines) < 20:
        return 0, '数据不足'
    closes = [k['close'] for k in resolved_klines]
    latest_close = closes[-1]
    
    def calc_rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains.append(max(d, 0)); losses.append(max(-d, 0))
        ag = sum(gains[-period:]) / period
        al = sum(losses[-period:]) / period
        if al == 0: return 100
        return 100 - (100 / (1 + ag / al))
    
    rsi = calc_rsi(closes)
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif = ema12[-1] - ema26[-1]
    dif_arr = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = _calc_ema(dif_arr, 9)[-1]
    macd_hist = 2 * (dif - dea)
    
    score = 0.0
    detail = ''
    
    # 买点
    buys = maidian.get('buy', [])
    if buys:
        buys_sorted = sorted(buys, key=lambda x: -x['strength'])
        best = buys_sorted[0]
        level_mult = {1: 1.0, 2: 0.7, 3: 0.5}
        cs = min(best['strength'] * level_mult.get(best['level'], 0.5), 3.0)
        score += cs
        detail += f"{best['name']} "
    else:
        score += 0
    
    # RSI
    if rsi < 30: score += 2.0
    elif rsi < 40: score += 1.5
    elif 40 <= rsi <= 60: score += 1.0
    elif 60 < rsi <= 70: score += 0.5
    else: score += 0
    
    # MACD
    if dif > 0 and macd_hist > 0: score += 2.0
    elif dif > 0 and macd_hist < 0 and macd_hist > -0.5: score += 1.5
    elif dif < 0 and macd_hist < 0: score += 0.5
    else: score += 1.0
    
    # 中枢位置
    if zhongshu_list:
        latest_z = zhongshu_list[-1]
        if latest_close > latest_z['zg']: score += 2.0
        elif latest_close > latest_z['zd']: score += 1.0
        else: score += 0
    else:
        score += 1.0
    
    return min(round(score, 1), 10.0), detail


# ===== 四维打分 =====
def four_dimensional_score(chan_s, candle_s, volume_s, beichi_list, fenxings):
    """
    四维打分：缠论/蜡烛图/量价/真技术 各10分
    返回各维度分数和总分
    """
    # 缠论维 (chan_s already 0-10)
    # 蜡烛图维：信号映射
    candle_map = {'bullish': (9, 10), 'neutral': (4, 6), 'bearish': (0, 3)}
    c_lo, c_hi = candle_map.get(candle_s['signal'], (4, 6))
    # 结合形态强度调整
    c_score = c_hi if candle_s['signal'] == 'bullish' else c_lo
    for p in candle_s.get('patterns', []):
        if '底反' in p or '三白兵' in p or '看涨' in p:
            c_score = max(c_score, 8)
        elif '顶反' in p or '三乌鸦' in p or '看跌' in p:
            c_score = min(c_score, 3)
    
    # 量价维 (volume_s['score'] already 0-10)
    v_score = volume_s.get('score', 5)
    
    # 真技术维(综合)
    t_score = 0
    t_detail = []
    
    # 背驰信号
    if beichi_list:
        bc = beichi_list[0]
        if bc['type'] == '底背驰':
            t_score += 3
            t_detail.append('底背驰')
        elif bc['type'] == '顶背驰':
            t_score -= 2
            t_detail.append('顶背驰')
    
    # 分型
    if fenxings:
        last_fx = fenxings[-1]
        if last_fx['type'] == 'bottom':
            t_score += 2; t_detail.append('底分型')
        elif last_fx['type'] == 'top':
            t_score -= 1; t_detail.append('顶分型')
    
    # MACD
    if 'macd_dif' in candle_s:
        if candle_s['macd_dif'] > 0: t_score += 2; t_detail.append('DIF>0')
    
    # 约束范围
    t_score = max(0, min(10, 5 + t_score))
    
    total = round(chan_s + c_score + v_score + t_score, 1)
    
    return {
        '缠论': round(chan_s, 1),
        '蜡烛图': round(c_score, 1),
        '量价': round(v_score, 1),
        '真技术': round(t_score, 1),
        '总分': total,
        '满分': 40
    }


# ===== 主分析函数 =====
def analyze_timeframe(klines, name):
    """对单个时间级别执行完整分析"""
    print(f"\n{'='*50}")
    print(f"📊 {name} 分析中... ({len(klines)}根K线)")
    
    if len(klines) < 20:
        return None
    
    # 1. 缠论
    resolved = resolve_inclusion(klines)
    fenxings = find_fenxing(resolved)
    bis = identify_bi(resolved, min_bars=3)
    segs = identify_seg(bis)
    zhongshu_list = find_zhongshu(bis)
    macd_data = calc_macd_for_bis(resolved, bis)
    beichi_signals = find_beichi(bis, zhongshu_list, macd_data)
    maidian = find_maidian(bis, zhongshu_list, beichi_signals)
    
    # 2. 蜡烛图
    candle = analyze_candlestick(klines)
    
    # 3. 量价
    volume = analyze_volume_price(klines)
    
    # 4. 缠论评分
    chan_sc, chan_detail = chan_score(bis, zhongshu_list, beichi_signals, maidian, resolved)
    
    # MACD数据附加
    closes = [k['close'] for k in resolved]
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif_arr = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = _calc_ema(dif_arr, 9)
    candle['macd_dif'] = dif_arr[-1] if dif_arr else 0
    candle['macd_dea'] = dea[-1] if dea else 0
    candle['macd_hist'] = 2 * (dif_arr[-1] - dea[-1]) if dif_arr and dea else 0
    
    # RSI
    def calc_rsi(closes, period=14):
        if len(closes) < period + 1: return 50
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains.append(max(d, 0)); losses.append(max(-d, 0))
        ag = sum(gains[-period:]) / period
        al = sum(losses[-period:]) / period
        if al == 0: return 100
        return round(100 - (100 / (1 + ag / al)), 1)
    candle['rsi'] = calc_rsi(closes)
    
    return {
        'kline_count': len(klines),
        'chan': {
            'bi_count': len(bis),
            'seg_count': len(segs),
            'zhongshu_count': len(zhongshu_list),
            'beichi_signals': [{'type': b['type'], 'date': b['date'], 'desc': b['desc']} for b in beichi_signals[:3]],
            'maidian': {'buy': maidian.get('buy', [])[:2], 'sell': maidian.get('sell', [])[:2]},
            'latest_bi': {'type': bis[-1]['type'], 'date': bis[-1]['end_date'], 'price': bis[-1]['end_price']} if bis else None,
            'latest_fenxing': {'type': fenxings[-1]['type'], 'date': fenxings[-1]['date']} if fenxings else None,
            'score': chan_sc,
        },
        'candlestick': candle,
        'volume': volume,
    }


def main():
    code = '601899'
    name = '紫金矿业'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"🔍 开始分析 {name}({code}) @ {timestamp}")
    print("="*60)
    
    # 获取4个时间级别数据
    scales = {5: 500, 15: 400, 30: 300, 240: 120}
    timeframe_names = {5: '5分钟', 15: '15分钟', 30: '30分钟', 240: '日线'}
    
    results = {}
    kline_data = {}
    
    for scale, datalen in scales.items():
        fname = timeframe_names[scale]
        print(f"\n📥 正在获取 {fname} 数据...")
        klines = fetch_kline(code, scale, datalen)
        kline_data[fname] = klines
        print(f"  实际获取: {len(klines)} 根K线")
        if len(klines) >= 20:
            r = analyze_timeframe(klines, fname)
            results[fname] = r
        else:
            print(f"  ⚠️ {fname}数据不足({len(klines)}根)，跳过分析")
            results[fname] = None
    
    # === 综合汇总 ===
    print("\n\n" + "="*70)
    print("📊 四维分析汇总")
    print("="*70)
    
    # 确定主方向
    up_count = 0
    down_count = 0
    total_score = 0
    valid_levels = []
    
    for fname, r in results.items():
        if r is None:
            continue
        valid_levels.append(fname)
        # 以缠论+MACD为主
        latest_bi = r['chan'].get('latest_bi')
        if latest_bi:
            if latest_bi['type'] == 'up':
                up_count += 1
            else:
                down_count += 1
        macd = r['candlestick']['macd_hist']
        if macd > 0:
            up_count += 0.5
        elif macd < 0:
            down_count += 0.5
    
    trend = '上涨' if up_count > down_count else ('下跌' if down_count > up_count else '震荡')
    
    # 汇总评分
    chan_total = 0
    candle_total = 0
    vol_total = 0
    tech_total = 0
    
    for fname, r in results.items():
        if r is None:
            continue
        cs = r['chan']['score']
        c_sig = r['candlestick']['signal']
        c_map = {'bullish': 9, 'neutral': 5, 'bearish': 2}
        c_s = c_map.get(c_sig, 5)
        v_s = r['volume']['score']
        t_s = 5.0
        if r['chan']['beichi_signals']:
            bc = r['chan']['beichi_signals'][0]
            if bc['type'] == '底背驰':
                t_s = 8.5
            elif bc['type'] == '顶背驰':
                t_s = 2.5
        if r['chan']['latest_fenxing']:
            fx = r['chan']['latest_fenxing']
            if fx['type'] == 'bottom':
                t_s = max(t_s, 7.0)
            elif fx['type'] == 'top':
                t_s = min(t_s, 3.5)
        
        chan_total += cs
        candle_total += c_s
        vol_total += v_s
        tech_total += t_s
    
    n = max(len(valid_levels), 1)
    avg_scores = {
        '缠论': round(chan_total / n, 1),
        '蜡烛图': round(candle_total / n, 1),
        '量价': round(vol_total / n, 1),
        '真技术': round(tech_total / n, 1),
    }
    avg_scores['总分'] = round(sum(avg_scores.values()), 1)
    
    print(f"\n四维平均评分（{len(valid_levels)}个级别）:")
    for k, v in avg_scores.items():
        print(f"  {k}: {v}")
    
    # === 确定买卖点 ===
    primary_buy = None
    primary_signal = 'neutral'
    
    # 从缠论找最近买点
    for fname in ['日线', '30分钟', '15分钟', '5分钟']:
        r = results.get(fname)
        if r is None:
            continue
        buys = r['chan']['maidian'].get('buy', [])
        if buys:
            primary_buy = buys[0]
            primary_signal = 'buy'
            break
    
    # 从蜡烛图判断
    for fname in ['日线', '30分钟', '15分钟', '5分钟']:
        r = results.get(fname)
        if r is None:
            continue
        if r['candlestick']['signal'] == 'bullish':
            primary_signal = 'buy'
            break
        elif r['candlestick']['signal'] == 'bearish':
            primary_signal = 'sell'
            break
    
    # === 计算止损和目标 ===
    daily = results.get('日线')
    if daily:
        latest_close = daily['candlestick']['last_bar']['close']
        ma5 = sum(k['close'] for k in kline_data['日线'][-5:]) / 5 if len(kline_data['日线']) >= 5 else latest_close
        ma20 = sum(k['close'] for k in kline_data['日线'][-20:]) / 20 if len(kline_data['日线']) >= 20 else latest_close
        
        # 缠论买点价位
        buy_price = latest_close
        if primary_buy and 'price' in primary_buy:
            buy_price = primary_buy['price']
        
        # 止损：取近期低点或-5%
        recent_lows = sorted([k['low'] for k in kline_data['日线'][-10:]])[:2]
        stop_loss = min(recent_lows) if recent_lows else round(latest_close * 0.95, 2)
        
        # 目标：上方压力位
        recent_highs = [k['high'] for k in kline_data['日线'][-20:]]
        resistance = max(recent_highs) if recent_highs else round(latest_close * 1.05, 2)
        
        # 更合理的目标
        target = round(latest_close * 1.10, 2)  # 默认10%目标
        
        if primary_signal == 'buy':
            # 最近支撑下方
            stop_loss_price = round(stop_loss * 0.99, 2)
            target_price = round(min(resistance, latest_close * 1.10), 2)
        else:
            stop_loss_price = round(latest_close * 0.98, 2)
            target_price = round(latest_close * 1.05, 2)
    else:
        latest_close = 0
        stop_loss_price = 0
        target_price = 0
    
    # === 简报 ===
    rsi_d = daily['candlestick']['rsi'] if daily else 50
    macd_d = daily['candlestick']['macd_hist'] if daily else 0
    candle_sig = daily['candlestick']['signal'] if daily else 'neutral'
    
    if avg_scores['总分'] >= 30:
        recommendation = '建议买入'
    elif avg_scores['总分'] >= 24:
        recommendation = '谨慎买入'
    elif avg_scores['总分'] >= 18:
        recommendation = '观望'
    else:
        recommendation = '建议观望/轻仓'
    
    brief_parts = []
    if trend == '上涨':
        brief_parts.append(f"当前{trend}趋势")
    if rsi_d < 40:
        brief_parts.append(f"RSI偏低({rsi_d})存在反弹机会")
    elif rsi_d > 70:
        brief_parts.append(f"RSI偏高({rsi_d})注意回调风险")
    if macd_d > 0:
        brief_parts.append("MACD多头排列")
    if primary_buy:
        brief_parts.append(f"存在{primary_buy.get('name', '买点')}信号")
    if not brief_parts:
        brief_parts.append("各指标中性，等待方向明确")
    
    brief = "；".join(brief_parts)
    
    # === 汇总各维度数据 ===
    analysis_summary = {}
    for fname, r in results.items():
        if r is None:
            analysis_summary[fname] = {
                '笔数': 0, '中枢': 0, '背驰': '无', '分型': '无', '买卖点': '无', '评分': 0
            }
            continue
        
        latest_bi = r['chan'].get('latest_bi')
        latest_fx = r['chan'].get('latest_fenxing')
        beichi = r['chan'].get('beichi_signals', [])
        buys = r['chan']['maidian'].get('buy', [])
        
        bi_type = latest_bi['type'] if latest_bi else '未知'
        fx_type = latest_fx['type'] if latest_fx else '无'
        beichi_type = beichi[0]['type'] if beichi else '无'
        buy_point = buys[0]['name'] if buys else '无'
        
        # 计算该级别评分
        cs = r['chan']['score']
        c_sig = r['candlestick']['signal']
        c_map = {'bullish': 9, 'neutral': 5, 'bearish': 2}
        c_s = c_map.get(c_sig, 5)
        v_s = r['volume']['score']
        
        level_score = round((cs + c_s + v_s + 5.0) / 4, 1)  # 0-10
        
        analysis_summary[fname] = {
            '笔数': r['chan']['