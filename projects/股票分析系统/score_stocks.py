# -*- coding: utf-8 -*-
"""
四维打分脚本 v2.0
缠论（结构）+ 蜡烛图（时机）+ 量价（能量）+ 真技术（心法）

更新日志：
v1.0: 简化蜡烛图打分
v2.0: 升级蜡烛图打分（考虑趋势背景+RSI+笔方向）
"""

import requests
import sys
import json
from projects.股票分析系统.chan_core import resolve_inclusion, find_fenxing, identify_bi, find_zhongshu, calc_macd_for_bis, find_beichi, calc_ema


def score_candle(fenx, bis, rsi):
    """
    蜡烛图维度打分（完整版）
    核心：位置决定有效性，不同事出信号天差地别
    """
    if not fenx or not bis:
        return 5, '无结构'
    
    last_fx = fenx[-1]
    fx_type = last_fx['type']
    last_bi = bis[-1]
    bi_direction = last_bi['type']
    
    # === 底部信号（买入参考）===
    if fx_type == 'bottom':
        if bi_direction == 'down' and rsi < 30:
            return 10, f'底/下/RSI={rsi:.0f}超卖'
        elif bi_direction == 'down' and rsi < 40:
            return 8, f'底/下/RSI={rsi:.0f}'
        elif bi_direction == 'down':
            return 7, f'底/下/RSI={rsi:.0f}'
        elif rsi < 40:
            return 7, f'底/上/RSI={rsi:.0f}'
        else:
            return 5, f'底/上/RSI={rsi:.0f}'
    
    # === 顶部信号（卖出参考）===
    elif fx_type == 'top':
        if bi_direction == 'up' and rsi > 70:
            return 3, f'顶/上/RSI={rsi:.0f}高位'
        elif bi_direction == 'up':
            return 4, f'顶/上/RSI={rsi:.0f}'
        else:
            return 5, f'顶/下/RSI={rsi:.0f}'
    
    return 5, '无分型'


def score_stock(name, sym):
    """
    单只股票四维打分
    返回: (name, pct, total, chan, candle, vol, tech, rsi, bi_count, zs_count, bc_count, candle_detail)
    """
    try:
        # 实时拉取数据
        r = requests.get(
            'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData',
            params={'symbol': sym, 'scale': '240', 'ma': 'no', 'datalen': 200},
            timeout=15
        )
        kl = sorted([
            {'date': b['day'],
             'open': float(b['open']),
             'close': float(b['close']),
             'high': float(b['high']),
             'low': float(b['low']),
             'volume': int(float(b.get('volume', 0)))}
            for b in r.json()
        ], key=lambda x: x['date'])
        
        # === 缠论结构 ===
        resolved = resolve_inclusion(kl)
        bis = identify_bi(resolved, 3)
        zs = find_zhongshu(bis)
        macd_data = calc_macd_for_bis(resolved, bis)
        beichi = find_beichi(bis, zs, macd_data)
        fenx = find_fenxing(resolved)
        
        # === 技术指标 ===
        closes = [k['close'] for k in resolved]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d for d in deltas[-14:] if d > 0]
        losses = [-d for d in deltas[-14:] if d < 0]
        ag = sum(gains) / 14 if gains else 0
        al = sum(losses) / 14 if losses else 0
        rsi = 100 - (100 / (1 + ag / al)) if al else 100
        
        ema12 = calc_ema(closes, 12)
        ema26 = calc_ema(closes, 26)
        dif = ema12[-1] - ema26[-1]
        dif_s = [ema12[i] - ema26[i] for i in range(len(closes))]
        dea = calc_ema(dif_s, 9)
        macd_h = 2 * (dif - dea[-1])
        
        last_bi = bis[-1] if bis else None
        last_fx = fenx[-1] if fenx else None
        
        # === 四维打分 ===
        # 缠论维度
        chan = 0
        if beichi and beichi[0]['type'] == '底背驰':
            chan = 10
        elif len(zs) > 0 and last_bi and last_bi['type'] == 'up':
            chan = 8
        elif last_bi:
            chan = 5
        
        # 蜡烛图维度
        candle, candle_detail = score_candle(fenx, bis, rsi)
        
        # 量价维度
        if rsi < 30:
            vol = 10
        elif rsi < 40:
            vol = 8
        elif rsi < 60:
            vol = 5
        else:
            vol = 3
        
        # 真技术维度
        if dif > 0 and macd_h > 0:
            tech = 10
        elif dif > 0:
            tech = 7
        elif macd_h < -0.5:
            tech = 3
        else:
            tech = 5
        
        total = chan + candle + vol + tech
        
        # 实时价格
        rq = requests.get(
            'https://hq.sinajs.cn/list=' + sym,
            headers={'Referer': 'https://finance.sina.com.cn'},
            timeout=8
        )
        parts = rq.text.split('"')[1].split(',')
        pct = (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100
        
        return (name, pct, total, chan, candle, vol, tech, rsi,
                len(bis), len(zs), len(beichi), last_fx['type'] if last_fx else '-',
                candle_detail)
    
    except Exception as e:
        return (name, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '-', f'err:{e}')


def main():
    with open('projects/股票分析系统/portfolio.json') as f:
        pf = json.load(f)
    
    results = []
    for code, info in pf.items():
        if info.get('hidden'):
            continue
        sym = 'sz' + code if not code.startswith('6') else 'sh' + code
        name = info.get('name', code)
        result = score_stock(name, sym)
        results.append(result)
    
    results.sort(key=lambda x: x[2], reverse=True)
    
    print('=' * 80)
    print('四维打分 v2.0（追踪池）')
    print('=' * 80)
    print(f'{"股票":<10} {"涨幅":>6} {"总分":>4} {"缠":>3} {"蜡":>3} {"量":>3} {"技":>3} {"RSI":>5} {"笔":>3} {"枢":>3} {"背驰":>4}')
    print('-' * 80)
    
    for r in results:
        name, pct, total, chan, candle, vol, tech, rsi, bi_n, zs_n, bc_n, fx_type, detail = r
        sig = '重仓' if total >= 32 else ('买' if total >= 20 else '观望')
        print(f'{name:<10} {pct:>+6.1f}% {total:>4}/40 {chan:>3} {candle:>3} {vol:>3} {tech:>3} {rsi:>5.0f} {bi_n:>3} {zs_n:>3} {bc_n:>4} {sig}')
    
    print()
    print('打分标准（每维度10分，满分40）：')
    print('  缠论: 底背驰=10 | 有中枢+向上笔=8 | 普通笔=5')
    print('  蜡烛图: 底分型+下跌+RSI<30=10 | 底分型+下跌+RSI<40=8 | 顶分型+上涨+RSI>70=3')
    print('  量价: RSI<30=10 | RSI<40=8 | RSI<60=5 | RSI>60=3')
    print('  真技术: DIF>0+MACD柱>0=10 | DIF>0=7 | DIF<0+MACD柱<-0.5=3')


if __name__ == '__main__':
    main()
