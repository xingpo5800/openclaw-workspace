# -*- coding: utf-8 -*-
"""
601899 紫金矿业 - 多级别缠论+蜡烛图+量价综合分析
5分钟 / 15分钟 / 30分钟 / 日线 四个级别
"""
import requests
import json
import math
import time
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '/Users/kevin/.openclaw/workspace/projects/股票分析系统')
from chan_core import (
    resolve_inclusion, find_fenxing, identify_bi, identify_seg,
    find_zhongshu, calc_macd_for_bis, find_beichi, find_maidian
)

STOCK_CODE = '601899'
STOCK_NAME = '紫金矿业'
CURRENT_PRICE = 33.01  # 从行情获取

# ========== 数据获取 ==========
def fetch_kline_eastmoney(secid, period, days=120):
    """从东方财富获取K线数据"""
    # period: 1=1分钟, 5=5分钟, 15=15分钟, 30=30分钟, 101=日K
    klt_map = {'1': 1, '5': 5, '15': 15, '30': 30, '60': 60, '101': 101}
    klt = klt_map.get(str(period), 101)
    
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": klt,
        "fqt": "1",
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
    if code.startswith('6'):
        return f"1.{code}"
    else:
        return f"0.{code}"


# ========== 蜡烛图分析 ==========
def candle_analysis(klines):
    """蜡烛图形态分析"""
    if len(klines) < 5:
        return {'pattern': '数据不足', 'signal': 'neutral', 'score': 5}
    
    recent = klines[-5:]
    last = recent[-1]
    prev = recent[-2]
    
    body = abs(last['close'] - last['open'])
    full_range = last['high'] - last['low']
    upper_shadow = last['high'] - max(last['open'], last['close'])
    lower_shadow = min(last['open'], last['close']) - last['low']
    
    is_bullish = last['close'] > last['open']
    
    # 基础分型判断
    if len(klines) >= 3:
        prev2 = klines[-3]
        mid = klines[-2]
        if is_bullish and mid['low'] < prev2['low'] and mid['low'] < last['low']:
            fenxing_type = '底分型'
        elif not is_bullish and mid['high'] > prev2['high'] and mid['high'] > last['high']:
            fenxing_type = '顶分型'
        else:
            fenxing_type = '无明确分型'
    else:
        fenxing_type = '数据不足'
    
    # 形态识别
    pattern = '正常K线'
    signal = 'neutral'
    score = 5
    
    if full_range > 0:
        body_ratio = body / full_range
        
        # 锤子线（长下影）
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            pattern = '锤子线(底)'
            signal = 'bullish'
            score = 8
        # 上吊线（长上影）
        elif upper_shadow > body * 2 and lower_shadow < body * 0.5:
            pattern = '上吊线(顶)'
            signal = 'bearish'
            score = 3
        # 吞没形态
        elif len(recent) >= 2:
            prev_k = recent[-2]
            prev_body = abs(prev_k['close'] - prev_k['open'])
            if is_bullish and prev_k['close'] < prev_k['open'] and last['close'] > prev_k['open'] and last['open'] < prev_k['close']:
                pattern = '看涨吞没'
                signal = 'bullish'
                score = 8
            elif not is_bullish and prev_k['close'] > prev_k['open'] and last['close'] < prev_k['close'] and last['open'] > prev_k['open']:
                pattern = '看跌吞没'
                signal = 'bearish'
                score = 3
        # 十字星
        if body_ratio < 0.2 and upper_shadow > body and lower_shadow > body:
            pattern = '十字星'
            signal = 'neutral'
            score = 5
        # 实体强
        elif body_ratio > 0.7:
            if is_bullish:
                pattern = '大阳线'
                signal = 'bullish'
                score = 7
            else:
                pattern = '大阴线'
                signal = 'bearish'
                score = 4
    
    # 连续K线
    consecutive = 0
    for k in reversed(recent):
        if (k['close'] > k['open']) == is_bullish:
            consecutive += 1
        else:
            break
    
    return {
        'pattern': pattern,
        'signal': signal,
        'score': score,
        'fenxing': fenxing_type,
        'body_ratio': round(body_ratio, 2) if full_range > 0 else 0,
        'consecutive': consecutive,
        'upper_shadow': round(upper_shadow, 3),
        'lower_shadow': round(lower_shadow, 3),
    }


# ========== 量价分析 ==========
def volume_price_analysis(klines, period_label=''):
    """量价综合分析"""
    if len(klines) < 10:
        return {}
    
    closes = [k['close'] for k in klines]
    volumes = [k['volume'] for k in klines]
    
    def ma(data, n):
        if len(data) < n:
            return None
        return sum(data[-n:]) / n
    
    # 不同周期使用不同均线参数
    if period_label == '日线':
        vol_n1, vol_n2 = 5, 60
        price_n1, price_n2 = 5, 20
    elif period_label == '30分钟':
        vol_n1, vol_n2 = 5, 20
        price_n1, price_n2 = 5, 20
    else:
        vol_n1, vol_n2 = 5, 20
        price_n1, price_n2 = 5, 20
    
    ma5_vol = ma(volumes, vol_n1)
    ma20_vol = ma(volumes, vol_n2)
    ma5_price = ma(closes, price_n1)
    ma20_price = ma(closes, price_n2)
    
    # 量能斜率
    n = min(20, len(volumes))
    if n >= 5:
        recent = volumes[-n:]
        x = list(range(n))
        y = recent
        x_mean = (n - 1) / 2
        y_mean = sum(y) / n
        num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        den = sum((x[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        vol_slope_norm = slope / (y_mean * 0.1) if y_mean else 0
    else:
        slope = 0
        vol_slope_norm = 0
    
    today_vol = volumes[-1]
    vol_ratio_5 = today_vol / ma5_vol if ma5_vol else 0
    vol_ratio_60 = today_vol / ma20_vol if ma20_vol else 0
    
    # 近期涨跌
    if len(closes) >= 5:
        recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100
    else:
        recent_change = 0
    
    # 量价配合
    price_up = closes[-1] > closes[-2] if len(closes) >= 2 else False
    vol_up = volumes[-1] > volumes[-2] if len(volumes) >= 2 else False
    
    return {
        'ma5_vol': round(ma5_vol, 0) if ma5_vol else 0,
        'ma20_vol': round(ma20_vol, 0) if ma20_vol else 0,
        'vol_slope_norm': round(vol_slope_norm, 3),
        'vol_ratio_5': round(vol_ratio_5, 2),
        'vol_ratio_60': round(vol_ratio_60, 2),
        'recent_change': round(recent_change, 2),
        'price_up': price_up,
        'vol_up': vol_up,
    }


def vol_score(vp_data):
    """量价评分"""
    if not vp_data:
        return 5, '数据不足'
    
    score = 5
    details = []
    
    vr5 = vp_data.get('vol_ratio_5', 1)
    if vr5 >= 2.0:
        score += 2
        details.append(f"爆量({vr5:.1f}x)")
    elif vr5 >= 1.5:
        score += 1
        details.append(f"放量({vr5:.1f}x)")
    elif vr5 < 0.5:
        score -= 1
        details.append("缩量")
    
    slope = vp_data.get('vol_slope_norm', 0)
    if slope > 0.2:
        score += 1
        details.append("量能上升")
    elif slope < -0.2:
        score -= 1
        details.append("量能下降")
    
    if vp_data.get('price_up') and vr5 >= 1.2:
        score += 1.5
        details.append("价涨量增")
    elif vp_data.get('price_up') and vr5 < 0.8:
        score -= 1
        details.append("价涨量缩(背离)")
    
    score = max(0, min(score, 10))
    return round(score, 1), "; ".join(details)


# ========== 缠论分析 ==========
def chan_analysis(klines):
    """缠论完整分析"""
    if len(klines) < 20:
        return {
            'bi_count': 0, 'zhongshu_count': 0, 'beichi': '无',
            'fenxing': '数据不足', 'maidian': '数据不足',
            'score': 0, 'trend': 'unknown'
        }
    
    resolved = resolve_inclusion(klines)
    bis = identify_bi(resolved, min_bars=5)
    zhongshu_list = find_zhongshu(bis)
    
    if bis:
        macd_data = calc_macd_for_bis(resolved, bis)
        beichi_signals = find_beichi(bis, zhongshu_list, macd_data)
        maidian = find_maidian(bis, zhongshu_list, beichi_signals)
    else:
        beichi_signals = []
        maidian = {'buy': [], 'sell': []}
    
    # 分型判断
    if len(resolved) >= 3:
        p1, p2, p3 = resolved[-3], resolved[-2], resolved[-1]
        if p2['low'] < p1['low'] and p2['low'] < p3['low']:
            fenxing = '底分型'
        elif p2['high'] > p1['high'] and p2['high'] > p3['high']:
            fenxing = '顶分型'
        else:
            fenxing = '无明确分型'
    else:
        fenxing = '数据不足'
    
    # 背驰
    if beichi_signals:
        beichi = beichi_signals[0].get('type', '背驰')
    else:
        beichi = '无'
    
    # 买卖点
    if maidian['buy']:
        maidian_str = maidian['buy'][0].get('name', '买点')
    else:
        maidian_str = '无明确买点'
    
    # 趋势
    if bis:
        trend = bis[-1]['type']
    else:
        trend = 'unknown'
    
    # 缠论评分
    score = 5
    score += min(len(zhongshu_list), 2) * 0.5
    score += min(len(beichi_signals), 2) * 1.0
    if maidian['buy']:
        score += 1.5
    score = max(0, min(score, 10))
    
    return {
        'bi_count': len(bis),
        'zhongshu_count': len(zhongshu_list),
        'beichi': beichi,
        'fenxing': fenxing,
        'maidian': maidian_str,
        'score': round(score, 1),
        'trend': trend,
        'beichi_signals': beichi_signals[:2],
        'maidian_buy': maidian['buy'][:2],
    }


# ========== 整体评分 ==========
def four_dimension_score(chan_data, candle_data, vp_data, klines):
    """四维打分"""
    # 缠论分
    chan_s = chan_data.get('score', 5)
    
    # 蜡烛图分
    candle_s = candle_data.get('score', 5)
    
    # 量价分
    vol_s = vol_score(vp_data)[0]
    
    # 真技术分（简化版）
    true_s = 5
    if len(klines) >= 20:
        closes = [k['close'] for k in klines]
        
        # MACD简化
        def ema(data, n):
            k_fac = 2 / (n + 1)
            result = [data[0]]
            for d in data[1:]:
                result.append(d * k_fac + result[-1] * (1 - k_fac))
            return result
        
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        dif = [ema12[i] - ema26[i] for i in range(len(closes))]
        dea = ema(dif, 9)
        macd = [2 * (dif[i] - dea[i]) for i in range(len(dif))]
        
        if len(macd) >= 2:
            if macd[-1] > 0:
                true_s += 0.5
            if len(macd) >= 3 and macd[-1] > macd[-2] > macd[-3]:
                true_s += 1
        
        # 均线
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        if ma5 > ma20:
            true_s += 1
        elif ma5 < ma20:
            true_s -= 1
        
        # 布林带
        if len(closes) >= 20:
            ma_b = sum(closes[-20:]) / 20
            std = math.sqrt(sum((c - ma_b) ** 2 for c in closes[-20:]) / 20)
            upper = ma_b + 2 * std
            lower = ma_b - 2 * std
            if closes[-1] <= lower * 1.02:
                true_s += 1.5
            elif closes[-1] >= upper * 0.98:
                true_s -= 1.5
    
    true_s = max(0, min(true_s, 10))
    
    total = chan_s + candle_s + vol_s + true_s
    
    return {
        '缠论': chan_s, '蜡烛图': candle_s, '量价': vol_s, '真技术': true_s,
        '总分': round(total, 1)
    }


# ========== 主分析 ==========
def analyze_level(secid, period, period_label, days):
    """分析单个周期"""
    print(f"\n{'='*50}")
    print(f"📊 {period_label}分析...")
    
    klines = fetch_kline_eastmoney(secid, period, days)
    if not klines or len(klines) < 20:
        print(f"  ⚠️ {period_label}数据不足")
        return None
    
    print(f"  获取 {len(klines)} 根K线, 时间范围: {klines[0]['date'][:10]} ~ {klines[-1]['date'][:10]}")
    
    # 缠论
    chan = chan_analysis(klines)
    print(f"  缠论: 笔={chan['bi_count']}, 中枢={chan['zhongshu_count']}, 背驰={chan['beichi']}, 分型={chan['fenxing']}, 买卖点={chan['maidian']}")
    
    # 蜡烛图
    candle = candle_analysis(klines)
    print(f"  蜡烛: {candle['pattern']}, 信号={candle['signal']}, 分型={candle['fenxing']}")
    
    # 量价
    vp = volume_price_analysis(klines, period_label)
    print(f"  量价: vol_ratio_5={vp.get('vol_ratio_5',0):.2f}, vol_slope={vp.get('vol_slope_norm',0):.3f}")
    
    # 四维
    scores = four_dimension_score(chan, candle, vp, klines)
    print(f"  四维: 缠论={scores['缠论']}, 蜡烛={scores['蜡烛图']}, 量价={scores['量价']}, 真技术={scores['真技术']}, 总分={scores['总分']}")
    
    return {
        'period_label': period_label,
        'klines_count': len(klines),
        'chan': chan,
        'candle': candle,
        'vp': vp,
        'scores': scores,
        'last_price': klines[-1]['close'] if klines else 0,
        'last_date': klines[-1]['date'][:16] if klines else '',
    }


# ========== 生成综合建议 ==========
def generate_advice(all_levels, stock_name):
    """综合四个级别生成建议"""
    total_score = sum(l['scores']['总分'] for l in all_levels if l) / len(all_levels) if all_levels else 0
    
    # 各级别得分
    level_scores = [l['scores']['总分'] for l in all_levels if l]
    up_count = sum(1 for l in all_levels if l and l['chan'].get('trend') == 'up')
    down_count = sum(1 for l in all_levels if l and l['chan'].get('trend') == 'down')
    
    # 背驰信号
    beichi_count = sum(len(l['chan'].get('beichi_signals', [])) for l in all_levels if l)
    
    # 买点数量
    buy_count = sum(len(l['chan'].get('maidian_buy', [])) for l in all_levels if l)
    
    # 综合建议
    if total_score >= 28 and buy_count >= 2:
        advice = "强烈买入"
        action = "买入"
    elif total_score >= 24 and up_count >= 3:
        advice = "买入"
        action = "买入"
    elif total_score >= 20:
        advice = "谨慎买入"
        action = "观望"
    elif down_count >= 3:
        advice = "观望或卖出"
        action = "卖出"
    else:
        advice = "观望"
        action = "观望"
    
    # 止损止盈
    day_level = next((l for l in all_levels if l and l['period_label'] == '日线'), None)
    if day_level:
        last_p = day_level['last_price']
        stop_loss = round(last_p * 0.97, 2)  # -3%
        target1 = round(last_p * 1.05, 2)   # +5%
        target2 = round(last_p * 1.10, 2)   # +10%
    else:
        last_p = 33.01
        stop_loss = round(last_p * 0.97, 2)
        target1 = round(last_p * 1.05, 2)
        target2 = round(last_p * 1.10, 2)
    
    # 简报
    brief = f"{stock_name}（{STOCK_CODE}）当前{stock_name}综合评分{total_score:.1f}/40，"
    if up_count > down_count:
        brief += f"多级别呈现上涨趋势，"
    else:
        brief += f"部分级别呈现回调压力，"
    brief += f"背驰信号{beichi_count}个，买点信号{buy_count}个。"
    if beichi_count > 0:
        brief += "注意背驰可能的反转机会。"
    if total_score >= 24:
        brief += "整体偏强，可考虑分批建仓。"
    else:
        brief += "建议等待更明确信号。"
    
    return {
        'total_score': round(total_score, 1),
        'advice': action,
        'stop_loss': str(stop_loss),
        'target1': str(target1),
        'target2': str(target2),
        'brief': brief,
        'detail': advice,
    }


# ========== 主函数 ==========
def main():
    print(f"\n{'#'*60}")
    print(f"📈 {STOCK_NAME}（{STOCK_CODE}）多级别缠论综合分析")
    print(f"#{'#'*60}")
    
    secid = get_secid(STOCK_CODE)
    
    # 四个级别
    levels_config = [
        (5, '5分钟', 500),    # 5分钟K线，最多500根（约17天）
        (15, '15分钟', 500),  # 15分钟K线，最多500根（约31天）
        (30, '30分钟', 500), # 30分钟K线，最多500根（约62天）
        (101, '日线', 250),  # 日K线，最多250根（约1年）
    ]
    
    results = []
    for period, label, days in levels_config:
        result = analyze_level(secid, period, label, days)
        if result:
            results.append(result)
        time.sleep(0.5)
    
    # 综合建议
    if results:
        advice = generate_advice(results, STOCK_NAME)
        
        print(f"\n{'='*60}")
        print(f"📋 综合分析结果")
        print(f"{'='*60}")
        print(f"  四级总分平均: {advice['total_score']}/40")
        print(f"  建议: {advice['advice']} | {advice['detail']}")
        print(f"  止损: ¥{advice['stop_loss']} | 目标1: ¥{advice['target1']} | 目标2: ¥{advice['target2']}")
        print(f"  简报: {advice['brief']}")
        
        # 构建JSON结果
        analysis_json = {}
        for r in results:
            label = r['period_label']
            scores = r['scores']
            chan = r['chan']
            
            analysis_json[label] = {
                "笔数": chan.get('bi_count', 0),
                "中枢": chan.get('zhongshu_count', 0),
                "背驰": chan.get('beichi', '无'),
                "分型": chan.get('fenxing', '无'),
                "买卖点": chan.get('maidian', '无'),
                "评分": scores.get('总分', 0),
                "蜡烛形态": chan.get('fenxing', '无'),
                "量能比": r['vp'].get('vol_ratio_5', 0),
            }
        
        # 补充缺失级别
        for label in ['5分钟', '15分钟', '30分钟', '日线']:
            if label not in analysis_json:
                analysis_json[label] = {
                    "笔数": 0, "中枢": 0, "背驰": "无", "分型": "数据不足",
                    "买卖点": "无", "评分": 0
                }
        
        output = {
            "stock_code": STOCK_CODE,
            "stock_name": STOCK_NAME,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "analysis": analysis_json,
            "四维总分": advice['total_score'],
            "建议": advice['advice'],
            "止损": advice['stop_loss'],
            "目标": advice['target2'],
            "简报": advice['brief'],
        }
        
        return output
    else:
        return None


if __name__ == '__main__':
    result = main()
    if result:
        output_path = '/Users/kevin/.openclaw/workspace/projects/股票分析系统/web_app/results/212a3035.json'
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {output_path}")
