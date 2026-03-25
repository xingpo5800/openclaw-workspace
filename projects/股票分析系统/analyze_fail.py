#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析上穿失败案例，找出失败因子"""

import requests
import json

fail_cases = [
    ('2025-01-07', '艾比森', 'sz300389'),
    ('2025-12-26', '协鑫集成', 'sz002506'),
    ('2025-12-04', '大金重工', 'sz002487'),
    ('2025-08-14', '和展能源', 'sz000809'),
    ('2025-08-05', '大金重工', 'sz002487'),
    ('2025-07-23', '红星发展', 'sh600367'),
    ('2025-07-16', '润建股份', 'sz002929'),
    ('2025-09-04', '协鑫集成', 'sz002506'),
]

for target_date, name, sym in fail_cases:
    print(f'\n=== {name}({target_date}) 上穿失败 ===')
    
    # 获取足够长的历史数据
    r = requests.get('https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData', params={'symbol':sym,'scale':'240','ma':'no','datalen':500}, timeout=15)
    raw = r.json()
    if not raw:
        print('无数据')
        continue
    
    # API返回已经是日期排序的（ newest first）
    # 找目标日期附近的数据
    target_idx = None
    for i, b in enumerate(raw):
        if b['day'] == target_date:
            target_idx = i
            break
    
    if target_idx is None:
        print(f'未找到日期 {target_date}，最近日期: {raw[-1]["day"]}')
        continue
    
    # 获取前后几天的数据
    start_idx = max(0, target_idx - 1)
    end_idx = min(len(raw), target_idx + 3)
    
    for j in range(start_idx, end_idx):
        b = raw[j]
        today_close = float(b['close'])
        today_open = float(b['open'])
        today_high = float(b['high'])
        today_low = float(b['low'])
        today_vol = int(b.get('volume', 0))
        
        tag = '←目标' if b['day'] == target_date else ('次日' if j == target_idx + 1 else '前一日' if j == target_idx - 1 else '')
        
        amp = (today_high - today_low) / today_low * 100
        body = abs(today_close - today_open) / today_open * 100
        upper_shadow = (today_high - max(today_open, today_close)) / today_low * 100
        lower_shadow = (min(today_open, today_close) - today_low) / today_low * 100
        
        # 计算量能变化
        vol_w = today_vol / 10000
        if j + 1 < len(raw):
            prev_vol = int(raw[j+1].get('volume', 0))
            vol_chg = (today_vol - prev_vol) / prev_vol * 100 if prev_vol > 0 else 0
            vol_str = f'{vol_chg:+.0f}%'
        else:
            vol_str = 'N/A'
        
        print(f'{b["day"]} {tag:<4}  开{today_open:.2f} 高{today_high:.2f} 低{today_low:.2f} 收{today_close:.2f} 量{vol_w:.0f}万({vol_str}) 振{amp:.1f}% 影上{upper_shadow:.1f}%下{lower_shadow:.1f}%')
        
        # 计算次日涨跌
        if j + 1 < len(raw):
            next_close = float(raw[j+1]['close'])
            next_open = float(raw[j+1]['open'])
            chg = (next_close - today_close) / today_close * 100
            print(f'        次日: 开{next_open:.2f} 收{next_close:.2f} 涨跌{chg:+.1f}%')
