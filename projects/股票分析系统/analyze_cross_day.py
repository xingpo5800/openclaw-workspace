#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

pf = json.load(open('projects/股票分析系统/portfolio.json'))
all_signals = []

for code, info in pf.items():
    if info.get('hidden'):
        continue
    sym = 'sz' + code if not code.startswith('6') else 'sh' + code
    name = info.get('name', code)
    try:
        r = requests.get(
            'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData',
            params={'symbol': sym, 'scale': '240', 'ma': 'no', 'datalen': 500},
            timeout=20
        )
        raw = r.json()
        if not raw or len(raw) < 100:
            continue

        for i in range(65, len(raw) - 10):
            vols = []
            closes = []
            for b in raw[:i + 1]:
                v = b.get('volume')
                if v is None:
                    continue
                vols.append(int(float(v)))
                closes.append(float(b['close']))

            if len(vols) < 65 or len(closes) < 65:
                continue

            avg_5 = sum(vols[-5:]) / 5
            avg_60 = sum(vols[-60:]) / 60
            avg_5_prev = sum(vols[-10:-5]) / 5

            ratio = avg_5 / avg_60 if avg_60 > 0 else 0
            slope_5 = (avg_5 - avg_5_prev) / avg_5_prev * 100 if avg_5_prev > 0 else 0

            c = closes[-14:]
            deltas = []
            for j in range(1, len(c)):
                deltas.append(c[j] - c[j - 1])
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            ag = sum(gains) / 14 if gains else 0
            al = sum(losses) / 14 if losses else 0
            rsi = 100 - (100 / (1 + ag / al)) if al else 50
            pct_20 = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) >= 21 else 0

            if i + 1 < len(raw):
                vols_tmr = []
                for b in raw[:i + 2]:
                    v = b.get('volume')
                    if v is None:
                        continue
                    vols_tmr.append(int(float(v)))

                if len(vols_tmr) < 65:
                    continue

                avg_5_tmr = sum(vols_tmr[-5:]) / 5
                avg_60_tmr = sum(vols_tmr[-60:]) / 60
                ratio_tmr = avg_5_tmr / avg_60_tmr if avg_60_tmr > 0 else 0

                if 0.85 <= ratio < 0.98 and ratio_tmr >= 1.0 and slope_5 > 0:
                    buy_price = closes[-1]
                    # 上穿当天的数据（raw[i]是上穿前一天，raw[i+1]是上穿当天）
                    try:
                        cross_vol = int(float(raw[i + 1].get('volume', 0)))
                        cross_close = float(raw[i + 1]['close'])
                        cross_high = float(raw[i + 1]['high'])
                        cross_low = float(raw[i + 1]['low'])
                        prev_vol = int(float(raw[i].get('volume', 0)))
                        vol_chg = (cross_vol - prev_vol) / prev_vol * 100 if prev_vol > 0 else 0
                        cross_pct = (cross_close - buy_price) / buy_price * 100
                        cross_amp = (cross_high - cross_low) / cross_low * 100
                    except:
                        continue

                    future_pct = []
                    for j in range(3, 12):
                        if i + j < len(raw):
                            try:
                                p = float(raw[i + j]['close'])
                                future_pct.append((p - buy_price) / buy_price * 100)
                            except:
                                pass

                    max_gain = max(future_pct) if future_pct else 0

                    all_signals.append({
                        'name': name,
                        'date': raw[i]['day'],
                        'rsi': rsi,
                        'pct_20': pct_20,
                        'slope_5': slope_5,
                        'cross_pct': cross_pct,
                        'cross_vol_chg': vol_chg,
                        'cross_amp': cross_amp,
                        'max_gain': max_gain,
                        'success': max_gain > 5
                    })
    except Exception as e:
        pass

print('信号总数:', len(all_signals))

if all_signals:
    total = len(all_signals)
    base = sum(1 for r in all_signals if r['success']) / total * 100
    print('基准:', total, '次 | 成功率', f'{base:.1f}%\n')

    conds = [
        ('上穿当天涨幅>3%', lambda r: r['cross_pct'] > 3),
        ('上穿当天涨幅>5%', lambda r: r['cross_pct'] > 5),
        ('上穿当天涨幅>7%', lambda r: r['cross_pct'] > 7),
        ('上穿当天涨幅>10%', lambda r: r['cross_pct'] > 10),
        ('上穿当天量能>50%', lambda r: r['cross_vol_chg'] > 50),
        ('上穿当天量能>100%', lambda r: r['cross_vol_chg'] > 100),
        ('涨幅>3% + 量>50%', lambda r: r['cross_pct'] > 3 and r['cross_vol_chg'] > 50),
        ('涨幅>5% + 量>50%', lambda r: r['cross_pct'] > 5 and r['cross_vol_chg'] > 50),
        ('涨幅>5% + RSI<65', lambda r: r['cross_pct'] > 5 and r['rsi'] < 65),
        ('涨幅>5% + RSI<60', lambda r: r['cross_pct'] > 5 and r['rsi'] < 60),
        ('涨幅>3% + RSI<60 + 量>50%', lambda r: r['cross_pct'] > 3 and r['rsi'] < 60 and r['cross_vol_chg'] > 50),
        ('涨幅>5% + RSI<65 + 量>50%', lambda r: r['cross_pct'] > 5 and r['rsi'] < 65 and r['cross_vol_chg'] > 50),
        ('涨幅>5% + RSI<65 + 量>100%', lambda r: r['cross_pct'] > 5 and r['rsi'] < 65 and r['cross_vol_chg'] > 100),
        ('涨幅>3% + slope>30', lambda r: r['cross_pct'] > 3 and r['slope_5'] > 30),
        ('涨幅>5% + slope>30', lambda r: r['cross_pct'] > 5 and r['slope_5'] > 30),
        ('涨幅>5% + RSI<65 + slope>30', lambda r: r['cross_pct'] > 5 and r['rsi'] < 65 and r['slope_5'] > 30),
        ('涨幅>5% + RSI<60 + slope>30', lambda r: r['cross_pct'] > 5 and r['rsi'] < 60 and r['slope_5'] > 30),
        ('涨幅>5% + RSI<65 + 量>50% + slope>30', lambda r: r['cross_pct'] > 5 and r['rsi'] < 65 and r['cross_vol_chg'] > 50 and r['slope_5'] > 30),
    ]

    print(f'{"条件":<45} {"次数":>5} {"成功率":>8} {"平均最大涨幅":>12}')
    print('-' * 75)
    for nc, c in conds:
        f = [r for r in all_signals if c(r)]
        if len(f) >= 3:
            s = sum(1 for r in f if r['success'])
            rate = s / len(f) * 100
            avg = sum(r['max_gain'] for r in f) / len(f)
            ev = rate / 100 * avg - (1 - rate / 100) * 5
            m = '★★★' if rate >= 85 else ('★★' if rate >= 75 else ('★' if rate >= 70 else ''))
            print(f'{nc:<45} {len(f):>5} {rate:>7.1f}% {avg:>+11.1f}% {m} 期望:{ev:>+5.1f}%')
