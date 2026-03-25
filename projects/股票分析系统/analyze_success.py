#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析上穿成功案例，找出成功因子"""

import requests
import json

# 成功的案例
success_cases = [
    ('2026-03-04', '艾比森', 'sz300389'),
    ('2026-01-09', '大金重工', 'sz002487'),
    ('2025-11-18', '金现代', 'sz300830'),
    ('2025-11-10', '协鑫集成', 'sz002506'),
    ('2025-11-03', '德业股份', 'sh605117'),
    ('2025-08-13', '润建股份', 'sz002929'),
    ('2025-06-13', '协鑫集成', 'sz002506'),
    ('2025-06-12', '大金重工', 'sz002487'),
    ('2025-06-09', '腾景科技', 'sh688195'),
]

for target_date, name, sym in success_cases:
    print(f'\n=== {name}({target_date}) 上穿成功 ===')
    
    r = requests.get('https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData', params={'symbol':sym,'scale':'240','ma':'no','datalen':500}, timeout=15)
    raw = r.json()
    if not raw:
        continue
    
    for i, b in enumerate(raw):
        if b['day'] == target_date:
            today = b
            tomorrow = raw[i+1] if i+1 < len(raw) else None
            yesterday = raw[i-1] if i > 0 else None
            
            today_close = float(today['close'])
            today_open = float(today['open'])
            today_high = float(today['high'])
            today_low = float(today['low'])
            today_vol = int(today.get('volume', 0))
            
            amp = (today_high - today_low) / today_low * 100
            body = abs(today_close - today_open) / today_open * 100
            upper_shadow = (today_high - max(today_open, today_close)) / today_low * 100
            lower_shadow = (min(today_open, today_close) - today_low) / today_low * 100
            
            if yesterday:
                prev_vol = int(yesterday.get('volume', 0))
                vol_chg = (today_vol - prev_vol) / prev_vol * 100 if prev_vol > 0 else 0
            else:
                vol_chg = 0
            
            print(f'当天: {today["day"]} 开{today_open:.2f} 高{today_high:.2f} 低{today_low:.2f} 收{today_close:.2f} 量{today_vol/10000:.0f}万({vol_chg:+.0f}%)')
            print(f'振幅: {amp:.1f}% | 实体: {body:.1f}% | 上影: {upper_shadow:.1f}% | 下影: {lower_shadow:.1f}%')
            
            if tomorrow:
                tmr_close = float(tomorrow['close'])
                tmr_open = float(tomorrow['open'])
                chg = (tmr_close - today_close) / today_close * 100
                tmr_vol = int(tomorrow.get('volume', 0))
                tmr_vol_chg = (tmr_vol - today_vol) / today_vol * 100 if today_vol > 0 else 0
                print(f'次日: {tomorrow["day"]} 开{tmr_open:.2f} 收{tmr_close:.2f} 涨跌{chg:+.1f}% 量变化{tmr_vol_chg:+.0f}%')
            break
