#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫金矿业(601899) 四维深度分析 - 完整版
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
    klines = get_kline_sina(code, scale, datalen)
    if len(klines) < 20:
        klines = get_kline_ifzq(code, scale, datalen)
    return klines


# ===== 蜡烛图分析 =====
def analyze_candlestick(klines):
    if len(klines) < 5:
        return {'patterns': [], 'signal': 'neutral', 'signal_desc': '数据不足'}
    
    recent = klines[-20:] if len(klines) >= 20 else klines
    patterns = []
    signal = 'neutral'
    signal_desc = ''
    
    last5 = recent[-5:]
    last3 = recent[-3:]
    last1 = recent[-1]
    
    body = last1['close'] - last1['open']
    body_size = abs(body)
    range_size = last1['high'] - last1['low']
    upper_shadow = last1['high'] - max(last1['open'], last1['close'])
    lower_shadow = min(last1['open'], last1['close']) - last1['low']
    
    is_bullish = body > 0
    
    def three_bar_pattern(bars):
        if len(bars) < 3:
            return None
        b1, b2, b3 = bars[-3], bars[-2], bars[-1]
        if b1['close'] < b1['open'] and abs(b2['close'] - b2['open']) < (b2['high'] - b2['low']) * 0.3 and b3['close'] > b3['open']:
            if (b1['close'] - b1['open']) > abs(b2['high'] - b2['low']) * 0.5:
                return '早晨之星(底反)'
        if b1['close'] > b1['open'] and abs(b2['close'] - b2['open']) < (b2['high'] - b2['low']) * 0.3 and b3['close'] < b3['open']:
            if (b1['open'] - b1['close']) > abs(b2['high'] - b2['low']) * 0.5:
                return '黄昏之星(顶反)'
        if all(b['close'] < b['open'] for b in bars[-3:]) and len(bars) >= 3:
            closes = [b['close'] for b in bars[-3:]]
            if closes[2] < closes[1] < closes[0]:
                return '三乌鸦(顶反)'
        if all(b['close'] > b['open'] for b in bars[-3:]) and len(bars) >= 3:
            closes = [b['close'] for b in bars[-3:]]
            if closes[2] > closes[1] > closes[0]:
                return '三白兵(底反)'
        if len(bars) >= 2:
            prev, curr = bars[-2], bars[-1]
            if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                if curr['open'] < prev['low'] and curr['close'] > prev['high']:
                    return '看涨吞没(底反)'
            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                if curr['open'] > prev['high'] and curr['close'] < prev['low']:
                    return '看跌吞没(顶反)'
        return None
    
    pattern = three_bar_pattern(recent)
    if pattern:
        patterns.append(pattern)
        if '底反' in pattern or '看涨' in pattern:
            signal = 'bullish'
            signal_desc = pattern
        elif '顶反' in pattern or '看跌' in pattern:
            signal = 'bearish'
            signal_desc = pattern
    
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
    
    if len(klines) >= 5:
        ma5 = sum(k['close'] for k in klines[-5:]) / 5
        if abs(last1['close'] - ma5) / ma5 < 0.005:
            patterns.append(f'贴近5日均线({ma5:.2f})')
    
    if len(klines) >= 10:
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
    if len(klines) < 5:
        return {'signal': 'neutral', 'score': 0, 'details': {}}
    
    closes = [k['close'] for k in klines]
    volumes = [k['volume'] for k in klines]
    latest_close = closes[-1]
    latest_vol = volumes[-1]
    
    vol_ma5 = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else sum(volumes) / len(volumes)
    vol_ma10 = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else vol_ma5
    vol_ma20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else vol_ma10
    
    if len(volumes) >= 10:
        recent5_vol = sum(volumes[-5:])
        prev5_vol = sum(volumes[-10:-5])
        vol_slope = (recent5_vol - prev5_vol) / prev5_vol * 100 if prev5_vol > 0 else 0
    else:
        vol_slope = 0
    
    if len(closes) >= 10:
        price_slope = (closes[-1] - closes[-10]) / closes[-10] * 100
    elif len(closes) >= 5:
        price_slope = (closes[-1] - closes[-5]) / closes[-5] * 100
    else:
        price_slope = 0
    
    vol_ratio = latest_vol / vol_ma5 if vol_ma5 > 0 else 1
    vol_vs_60 = latest_vol / vol_ma20 if vol_ma20 > 0 else 1
    
    score = 0
    details = {}
    signal = 'neutral'
    
    if price_slope > 1 and vol_slope > 5 and vol_ratio > 1.2:
        score = 10; signal = 'bullish'
        details['判断'] = '量价齐升，强势'
    elif price_slope > 0.5 and vol_slope > 0:
        score = 8; signal = 'bullish'
        details['判断'] = '价升量稳，良好'
    elif price_slope > 0 and vol_slope > 10:
        score = 9; signal = 'bullish'
        details['判断'] = '放量上涨，活跃'
    elif abs(price_slope) < 1 and vol_slope < -10:
        score = 6; signal = 'neutral'
        details['判断'] = '缩量整理，观望'
    elif price_slope < -1 and vol_slope < 0:
        score = 4; signal = 'bearish'
        details['判断'] = '价跌量缩，偏弱'
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
    
    buys = maidian.get('buy', [])
    if buys:
        buys_sorted = sorted(buys, key=lambda x: -x['strength'])
        best = buys_sorted[0]
        level_mult = {1: 1.0, 2: 0.7, 3: 0.5}
        cs = min(best['strength'] * level_mult.get(best['level'], 0.5), 3.0)
        score += cs
        detail += f"{best['name']} "
    
    if rsi < 30: score += 2.0
    elif rsi < 40: score += 1.5
    elif 40 <= rsi <= 60: score += 1.0
    elif 60 < rsi <= 70: score += 0.5
    
    if dif > 0 and macd_hist > 0: score += 2.0
    elif dif > 0 and macd_hist < 0 and macd_hist > -0.5: score += 1.5
    elif dif < 0 and macd_hist < 0: score += 0.5
    else: score += 1.0
    
    if zhongshu_list:
        latest_z = zhongshu_list[-1]
        if latest_close > latest_z['zg']: score += 2.0
        elif latest_close > latest_z['zd']: score += 1.0
    else:
        score += 1.0
    
    return min(round(score, 1), 10.0), detail


# ===== 单级别分析 =====
def analyze_timeframe(klines, name):
    print(f"\n{'='*50}")
    print(f"📊 {name} 分析中... ({len(klines)}根K线)")
    
    if len(klines) < 20:
        return None
    
    resolved = resolve_inclusion(klines)
    fenxings = find_fenxing(resolved)
    bis = identify_bi(resolved, min_bars=3)
    segs = identify_seg(bis)
    zhongshu_list = find_zhongshu(bis)
    macd_data = calc_macd_for_bis(resolved, bis)
    beichi_signals = find_beichi(bis, zhongshu_list, macd_data)
    maidian = find_maidian(bis, zhongshu_list, beichi_signals)
    
    candle = analyze_candlestick(klines)
    volume = analyze_volume_price(klines)
    chan_sc, chan_detail = chan_score(bis, zhongshu_list, beichi_signals, maidian, resolved)
    
    closes = [k['close'] for k in resolved]
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif_arr = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = _calc_ema(dif_arr, 9)
    candle['macd_dif'] = dif_arr[-1] if dif_arr else 0
    candle['macd_dea'] = dea[-1] if dea else 0
    candle['macd_hist'] = 2 * (dif_arr[-1] - dea[-1]) if dif_arr and dea else 0
    
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
    
    up_count = 0
    down_count = 0
    valid_levels = []
    
    for fname, r in results.items():
        if r is None:
            continue
        valid_levels.append(fname)
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
    
    for fname in ['日线', '30分钟', '15分钟', '5分钟']:
        r = results.get(fname)
        if r is None:
            continue
        buys = r['chan']['maidian'].get('buy', [])
        if buys:
            primary_buy = buys[0]
            primary_signal = 'buy'
            break
    
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
        recent_lows = sorted([k['low'] for k in kline_data['日线'][-10:]])[:2]
        stop_loss = min(recent_lows) if recent_lows else round(latest_close * 0.95, 2)
        recent_highs = [k['high'] for k in kline_data['日线'][-20:]]
        resistance = max(recent_highs) if recent_highs else round(latest_close * 1.05, 2)
        
        if primary_signal == 'buy':
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
    
    # === 构建JSON结果 ===
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
        
        bi_type = '上涨' if latest_bi and latest_bi['type'] == 'up' else '下跌'
        fx_type = '底分型' if latest_fx and latest_fx['type'] == 'bottom' else ('顶分型' if latest_fx and latest_fx['type'] == 'top' else '无')
        beichi_type = beichi[0]['type'] if beichi else '无'
        buy_point = buys[0]['name'] if buys else '无'
        
        cs = r['chan']['score']
        c_sig = r['candlestick']['signal']
        c_map = {'bullish': 9, 'neutral': 5, 'bearish': 2}
        c_s = c_map.get(c_sig, 5)
        v_s = r['volume']['score']
        
        level_score = round((cs + c_s + v_s + 5.0) / 4, 1)
        
        analysis_summary[fname] = {
            '笔数': r['chan']['bi_count'],
            '中枢': r['chan']['zhongshu_count'],
            '背驰': beichi_type,
            '分型': fx_type,
            '买卖点': buy_point,
            '评分': level_score
        }
    
    final_result = {
        "stock_code": code,
        "stock_name": name,
        "timestamp": timestamp,
        "analysis": analysis_summary,
        "四维总分": avg_scores['总分'],
        "建议": recommendation,
        "止损": str(stop_loss_price),
        "目标": str(target_price),
        "简报": brief,
        "detail": {
            "缠论均分": avg_scores['缠论'],
            "蜡烛图均分": avg_scores['蜡烛图'],
            "量价均分": avg_scores['量价'],
            "真技术均分": avg_scores['真技术'],
            "趋势": trend,
            "RSI": rsi_d,
            "MACD柱": macd_d,
            "最新价": latest_close
        }
    }
    
    # 打印结果
    print(f"\n{'='*70}")
    print("📋 各周期汇总:")
    for fname, a in analysis_summary.items():
        print(f"  {fname}: 笔{a['笔数']}笔, 中枢{a['中枢']}个, {a['背驰']}, {a['分型']}, {a['买卖点']}, 评分{a['评分']}")
    
    print(f"\n💰 最新价: {latest_close}")
    print(f"📊 四维总分: {avg_scores['总分']}/40")
    print(f"🎯 建议: {recommendation}")
    print(f"🛡️ 止损: {stop_loss_price}")
    print(f"🎯 目标: {target_price}")
    print(f"\n📝 简报: {brief}")
    
    # 保存结果
    output_dir = '/Users/kevin/.openclaw/workspace/projects/股票分析系统/web_app/results'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, '32bdde5b.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存至: {output_file}")
    
    return final_result


if __name__ == '__main__':
    main()
