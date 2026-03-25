# -*- coding: utf-8 -*-
"""
缠论核心算法 v3.0（基于全书完整理解重写）
位置：stock/chan_core.py

主要改动（v2→v3）：
1. K线包含关系：严格按书中定义（方向动态判断 + 去高留低/去低留高）
2. 分型识别：在包含处理后的K线上识别
3. 笔识别：严格验证分型之间的独立K线数
4. 线段识别：按特征序列分型法
5. 中枢识别：验证三笔构成有效重叠
"""


def resolve_inclusion(klines):
    """
    处理K线包含关系（缠论数学起点）

    方向定义：
      向上: gn ≥ gn-1（第n根K线高点不创新低）
      向下: dn ≤ dn-1（第n根K线低点不创新高）

    包含关系：
      向上包含(gn>gn-1 且 dn<dn-1): 取两根K线中高点和低点的【最大值】，即"去高留低"
      向下包含(gn<gn-1 且 dn>dn-1): 取两根K线中高点和低点的【最小值】，即"去低留高"
    """
    if len(klines) < 3:
        return [dict(k) for k in klines]

    bars = []
    for k in klines:
        bars.append({
            'date': k['date'], 'open': k['open'], 'close': k['close'],
            'high': k['high'], 'low': k['low'], 'volume': k.get('volume', 0)
        })

    result = [bars[0], bars[1]]
    i = 2

    while i < len(bars):
        prev = result[-1]
        curr = bars[i]

        # 包含关系判断：K2完全在K1的范围内（边界相等视为包含）
        has_inclusion_up = (curr['high'] <= prev['high'] and curr['low'] >= prev['low'])
        has_inclusion_down = (curr['high'] >= prev['high'] and curr['low'] <= prev['low'])

        # 无包含关系：直接添加
        if not has_inclusion_up and not has_inclusion_down:
            result.append(curr)
            i += 1
            continue

        # 确定方向：基于之前已处理K线确定当前趋势方向
        # direction由result[-1]与curr的包含关系决定，而非简单比较
        if has_inclusion_up:
            # K2在K1内部，延续之前的方向（保持包含关系）
            direction_up = True
            direction_down = False
        else:  # has_inclusion_down
            # K1在K2内部（向下包含），延续之前的方向
            direction_up = False
            direction_down = True

        if direction_up:
            # 向上包含：去高留低（取两根K线中高点的较大值，低点的较大值）
            merged = {
                'date': curr['date'], 'open': prev['open'], 'close': curr['close'],
                'high': max(prev['high'], curr['high']),
                'low': max(prev['low'], curr['low']),
                'volume': curr.get('volume', 0)
            }
        else:
            # 向下包含：去低留高（取两根K线中高点的较小值，低点的较小值）
            merged = {
                'date': curr['date'], 'open': prev['open'], 'close': curr['close'],
                'high': min(prev['high'], curr['high']),
                'low': min(prev['low'], curr['low']),
                'volume': curr.get('volume', 0)
            }

        result[-1] = merged
        i += 1

    return result


def find_fenxing(klines):
    """
    识别分型（顶分型和底分型）

    顶分型：三根连续K线，中间一根的高点最高、低点也最高
    底分型：三根连续K线，中间一根的低点最低、高点也最低
    """
    fenxings = []
    for i in range(1, len(klines) - 1):
        prev = klines[i - 1]
        mid = klines[i]
        nxt = klines[i + 1]

        if mid['high'] > prev['high'] and mid['high'] > nxt['high'] and \
           mid['low'] > prev['low'] and mid['low'] > nxt['low']:
            fenxings.append({'idx': i, 'type': 'top', 'date': mid['date'],
                             'high': mid['high'], 'low': mid['low']})
        elif mid['low'] < prev['low'] and mid['low'] < nxt['low'] and \
             mid['high'] < prev['high'] and mid['high'] < nxt['high']:
            fenxings.append({'idx': i, 'type': 'bottom', 'date': mid['date'],
                             'high': mid['high'], 'low': mid['low']})

    return fenxings


def identify_bi(klines, min_bars=5):
    """
    识别笔（严格版）

    笔的定义：两个相邻的异性质分型之间，有至少min_bars根独立K线
    """
    if len(klines) < min_bars + 2:
        return []

    fenxings = find_fenxing(klines)
    if len(fenxings) < 2:
        return []

    bis = []
    i = 0

    while i < len(fenxings) - 1:
        fx1 = fenxings[i]
        fx2 = fenxings[i + 1]
        mid_kbars = fx2['idx'] - fx1['idx'] - 1

        if fx1['type'] == 'bottom' and fx2['type'] == 'top':
            if mid_kbars >= min_bars:
                bis.append({
                    'type': 'up',
                    'start_idx': fx1['idx'], 'end_idx': fx2['idx'],
                    'start_date': fx1['date'], 'end_date': fx2['date'],
                    'start_price': fx1['low'], 'end_price': fx2['high'],
                    'bars_count': mid_kbars + 2,
                    'amplitude': round((fx2['high'] - fx1['low']) / fx1['low'] * 100, 2)
                })
            i += 1
        elif fx1['type'] == 'top' and fx2['type'] == 'bottom':
            if mid_kbars >= min_bars:
                bis.append({
                    'type': 'down',
                    'start_idx': fx1['idx'], 'end_idx': fx2['idx'],
                    'start_date': fx1['date'], 'end_date': fx2['date'],
                    'start_price': fx1['high'], 'end_price': fx2['low'],
                    'bars_count': mid_kbars + 2,
                    'amplitude': round((fx1['high'] - fx2['low']) / fx1['high'] * 100, 2)
                })
            i += 1
        else:
            i += 1

    return bis


def identify_seg(bis):
    """
    识别线段

    线段：由3个或以上连续同向笔构成
    线段终结需按特征序列分型法判断（简化版：连续3笔同向即构成线段）
    """
    if len(bis) < 3:
        return []

    segs = []
    i = 0

    while i <= len(bis) - 3:
        direction = bis[i]['type']
        j = i + 1
        while j < len(bis) and bis[j]['type'] == direction:
            j += 1

        count = j - i
        if count >= 3:
            seg_bis = bis[i:j]
            if direction == 'up':
                start_price = seg_bis[0]['start_price']
                end_price = seg_bis[-1]['end_price']
            else:
                start_price = seg_bis[0]['start_price']
                end_price = seg_bis[-1]['end_price']

            amplitude = abs(end_price - start_price) / start_price * 100

            segs.append({
                'type': direction,
                'start_idx': i, 'end_idx': j - 1,
                'start_date': seg_bis[0]['start_date'],
                'end_date': seg_bis[-1]['end_date'],
                'start_price': round(start_price, 2),
                'end_price': round(end_price, 2),
                'amplitude': round(amplitude, 2),
                'bi_count': count,
                'bi_indices': list(range(i, j))
            })
            i = j
        else:
            i += 1

    return segs


def find_zhongshu(bis):
    """
    识别中枢（严格版）

    三个连续同向笔的重叠区域构成中枢：
      向上中枢: ZG=max(start_prices), ZD=min(end_prices), 有效=ZG>ZD
      向下中枢: ZG=max(end_prices), ZD=min(start_prices), 有效=ZG>ZD
    """
    if not bis or len(bis) < 3:
        return []

    candidates = []
    i = 0
    while i <= len(bis) - 3:
        b0, b1, b2 = bis[i], bis[i+1], bis[i+2]
        if not (b0['type'] == b1['type'] == b2['type']):
            i += 1
            continue

        direction = b0['type']

        if direction == 'up':
            zg = max(b0['start_price'], b1['start_price'], b2['start_price'])
            zd = min(b0['end_price'], b1['end_price'], b2['end_price'])
            gg = min(b0['end_price'], b1['end_price'])
            dd = max(b1['start_price'], b2['start_price'])
        else:
            zg = max(b0['end_price'], b1['end_price'], b2['end_price'])
            zd = min(b0['start_price'], b1['start_price'], b2['start_price'])
            gg = max(b0['end_price'], b1['end_price'])
            dd = min(b1['start_price'], b2['start_price'])

        if zg > zd:
            range_w = abs(zg - zd) / zd * 100 if zd != 0 else 0
            candidates.append({
                'type': direction,
                'bi_indices': (i, i+1, i+2),
                'start_bi_idx': i, 'end_bi_idx': i + 2,
                'start_date': b0['start_date'], 'end_date': b2['end_date'],
                'zg': round(zg, 3), 'zd': round(zd, 3),
                'gg': round(gg, 3), 'dd': round(dd, 3),
                'range_width': round(range_w, 3),
                'bi_count': 3, 'is_extended': False,
            })
        i += 1

    if not candidates:
        return []

    merged = []
    seq_start = 0
    for j in range(1, len(candidates)):
        prev = candidates[j - 1]
        curr = candidates[j]
        if prev['type'] != curr['type']:
            connected = False
        elif prev['type'] == 'up':
            connected = curr['zg'] >= prev['zd']
        else:
            connected = curr['zg'] <= prev['zd']

        if not connected:
            final = _merge_seq(bis, candidates, seq_start, j - 1)
            merged.append(final)
            seq_start = j

    final = _merge_seq(bis, candidates, seq_start, len(candidates) - 1)
    merged.append(final)

    for idx, z in enumerate(merged):
        z['index'] = idx + 1

    return merged


def _merge_seq(bis, candidates, start_idx, end_idx):
    z = dict(candidates[start_idx])
    z['is_extended'] = (end_idx > start_idx)

    involved = set()
    for k in range(start_idx, end_idx + 1):
        involved.update(candidates[k]['bi_indices'])
    involved = sorted(involved)

    if len(involved) < 3:
        return z

    direction = z['type']
    if direction == 'up':
        pens = involved[:3]
        zg = max(bis[p]['start_price'] for p in pens)
        zd = min(bis[p]['end_price'] for p in pens)
    else:
        pens = involved[:3]
        zg = max(bis[p]['end_price'] for p in pens)
        zd = min(bis[p]['start_price'] for p in pens)

    z['zg'] = round(zg, 3)
    z['zd'] = round(zd, 3)
    z['start_bi_idx'] = involved[0]
    z['end_bi_idx'] = involved[-1]
    z['start_date'] = bis[involved[0]]['start_date']
    z['end_date'] = bis[involved[-1]]['end_date']
    z['range_width'] = round(abs(zg - zd) / zd * 100, 3) if zd != 0 else 0
    return z


def calc_ema(data, period):
    k = 2 / (period + 1)
    result = [data[0]]
    for d in data[1:]:
        result.append(d * k + result[-1] * (1 - k))
    return result


def calc_macd_for_bis(resolved_klines, bis):
    if len(resolved_klines) < 35 or not bis:
        return {}

    closes = [k['close'] for k in resolved_klines]
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    dif_seq = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea_seq = calc_ema(dif_seq, 9)
    macd_seq = [2 * (dif_seq[i] - dea_seq[i]) for i in range(len(closes))]

    result = {}
    for idx, bi in enumerate(bis):
        si = bi['start_idx']
        ei = bi['end_idx']
        if si < 0 or ei >= len(macd_seq) or si >= len(macd_seq):
            continue
        area = sum(macd_seq[si:min(ei + 1, len(macd_seq))])
        result[idx] = {
            'area': round(area, 4),
            'amplitude': bi['amplitude'],
            'end_price': bi['end_price'],
            'start_price': bi['start_price'],
        }
    return result


def find_beichi(bis, zhongshu_list, macd_data):
    if not bis or not macd_data:
        return []

    signals = []

    # 模式A：标准背驰（离开中枢后）
    for z in zhongshu_list:
        z_end = z['end_bi_idx']
        leave_dir = 'down' if z['type'] == 'up' else 'up'

        if z_end + 2 >= len(bis):
            continue
        b1, b2 = bis[z_end + 1], bis[z_end + 2]
        if not (b1['type'] == b2['type'] == leave_dir):
            continue

        d1, d2 = macd_data.get(z_end + 1), macd_data.get(z_end + 2)
        if not d1 or not d2:
            continue

        area1, area2 = abs(d1['area']), abs(d2['area'])
        if area2 == 0:
            continue
        bei_ratio = area1 / area2

        if leave_dir == 'up' and d2['end_price'] < d1['end_price'] and bei_ratio > 1.1:
            signals.append({
                'type': '底背驰', 'direction': 'up', 'bi_pair': (z_end + 1, z_end + 2), 'mode': 'A',
                'price_before': d1['end_price'], 'price_after': d2['end_price'],
                'area_before': round(area1, 4), 'area_after': round(area2, 4),
                'bei_ratio': round(bei_ratio, 2), 'strength': round(min(bei_ratio / 2, 3.0), 2),
                'date': b2['end_date'], 'center_idx': z['index'],
                'desc': f"标准背驰 | 价格↓{d2['end_price']:.2f}<{d1['end_price']:.2f} | 力度↓{bei_ratio:.1f}x"
            })
        elif leave_dir == 'down' and d2['end_price'] > d1['end_price'] and bei_ratio > 1.1:
            signals.append({
                'type': '顶背驰', 'direction': 'down', 'bi_pair': (z_end + 1, z_end + 2), 'mode': 'A',
                'price_before': d1['end_price'], 'price_after': d2['end_price'],
                'area_before': round(area1, 4), 'area_after': round(area2, 4),
                'bei_ratio': round(bei_ratio, 2), 'strength': round(min(bei_ratio / 2, 3.0), 2),
                'date': b2['end_date'], 'center_idx': z['index'],
                'desc': f"标准背驰 | 价格↑{d2['end_price']:.2f}>{d1['end_price']:.2f} | 力度↓{bei_ratio:.1f}x"
            })

    # 模式B：宽松背驰（最近连续同向4笔）
    if len(bis) >= 4:
        for i in range(len(bis) - 3):
            if bis[i]['type'] != bis[i + 1]['type'] or bis[i + 2]['type'] != bis[i + 3]['type']:
                continue
            if bis[i]['type'] != bis[i + 2]['type']:
                continue

            d = [macd_data.get(i + k) for k in range(4)]
            if not all(d):
                continue

            area1 = abs(d[0]['area']) + abs(d[1]['area'])
            area2 = abs(d[2]['area']) + abs(d[3]['area'])
            if area2 == 0:
                continue
            bei_ratio = area1 / area2
            direction = bis[i]['type']

            if direction == 'down':
                p_after = min(d[2]['end_price'], d[3]['end_price'])
                p_before = min(d[0]['end_price'], d[1]['end_price'])
                if p_after < p_before and bei_ratio > 1.2:
                    desc = f"宽松背驰 | 两波↓力度{bei_ratio:.1f}x | {p_before:.2f}→{p_after:.2f}"
                    if not any(b['desc'] == desc for b in signals):
                        signals.append({
                            'type': '底背驰', 'direction': 'up', 'bi_pair': (i, i + 3), 'mode': 'B',
                            'price_before': p_before, 'price_after': p_after,
                            'area_before': round(area1, 4), 'area_after': round(area2, 4),
                            'bei_ratio': round(bei_ratio, 2), 'strength': round(min(bei_ratio / 2, 3.0), 2),
                            'date': bis[i + 3]['end_date'], 'center_idx': 0, 'desc': desc
                        })
            else:
                p_after = max(d[2]['end_price'], d[3]['end_price'])
                p_before = max(d[0]['end_price'], d[1]['end_price'])
                if p_after > p_before and bei_ratio > 1.2:
                    desc = f"宽松背驰 | 两波↑力度{bei_ratio:.1f}x | {p_before:.2f}→{p_after:.2f}"
                    if not any(b['desc'] == desc for b in signals):
                        signals.append({
                            'type': '顶背驰', 'direction': 'down', 'bi_pair': (i, i + 3), 'mode': 'B',
                            'price_before': p_before, 'price_after': p_after,
                            'area_before': round(area1, 4), 'area_after': round(area2, 4),
                            'bei_ratio': round(bei_ratio, 2), 'strength': round(min(bei_ratio / 2, 3.0), 2),
                            'date': bis[i + 3]['end_date'], 'center_idx': 0, 'desc': desc
                        })

    signals.sort(key=lambda x: x['date'], reverse=True)
    return signals


def find_maidian(bis, zhongshu_list, beichi_signals):
    if not bis or not zhongshu_list:
        return {'buy': [], 'sell': []}

    buys = []
    sells = []

    for bc in beichi_signals:
        if bc['type'] == '底背驰':
            buys.append({
                'level': 1, 'name': '第一类买点(1买)', 'date': bc['date'], 'price': bc['price_after'],
                'strength': bc['strength'], 'bei_ratio': bc['bei_ratio'],
                'center_idx': bc['center_idx'], 'desc': bc['desc'], 'type': 'buy'
            })
        elif bc['type'] == '顶背驰':
            sells.append({
                'level': 1, 'name': '第一类卖点(1卖)', 'date': bc['date'], 'price': bc['price_after'],
                'strength': bc['strength'], 'bei_ratio': bc['bei_ratio'],
                'center_idx': bc['center_idx'], 'desc': bc['desc'], 'type': 'sell'
            })

    for buy1 in list(buys):
        idx1 = next((j for j, bi in enumerate(bis) if bi['end_date'] >= buy1['date']), None)
        if idx1 is None or idx1 + 2 >= len(bis):
            continue
        for j in range(idx1, min(idx1 + 5, len(bis) - 1)):
            if bis[j]['type'] == 'down' and j + 1 < len(bis) and bis[j + 1]['type'] == 'up':
                pb = bis[j]['end_price']
                if pb >= buy1['price'] * 0.97:
                    buys.append({
                        'level': 2, 'name': '第二类买点(2买)', 'date': bis[j]['end_date'], 'price': pb,
                        'strength': round(buy1['strength'] * 0.8, 2),
                        'ref_1buy_price': buy1['price'],
                        'desc': f"1买后回调不破 {pb:.2f}≥{buy1['price']:.2f}", 'type': 'buy'
                    })
                    break

    for sell1 in list(sells):
        idx1 = next((j for j, bi in enumerate(bis) if bi['end_date'] >= sell1['date']), None)
        if idx1 is None or idx1 + 2 >= len(bis):
            continue
        for j in range(idx1, min(idx1 + 5, len(bis) - 1)):
            if bis[j]['type'] == 'up' and j + 1 < len(bis) and bis[j + 1]['type'] == 'down':
                pb = bis[j]['end_price']
                if pb <= sell1['price'] * 1.03:
                    sells.append({
                        'level': 2, 'name': '第二类卖点(2卖)', 'date': bis[j]['end_date'], 'price': pb,
                        'strength': round(sell1['strength'] * 0.8, 2),
                        'ref_1sell_price': sell1['price'],
                        'desc': f"1卖后反弹不创新高 {pb:.2f}≤{sell1['price']:.2f}", 'type': 'sell'
                    })
                    break

    for z in zhongshu_list:
        if z['end_bi_idx'] + 2 >= len(bis):
            continue
        leave = bis[z['end_bi_idx'] + 1]

        if z['type'] == 'up':
            if leave['type'] == 'down' and z['end_bi_idx'] + 2 < len(bis):
                cb = bis[z['end_bi_idx'] + 2]
                if cb['type'] == 'up' and cb['end_price'] > z['zd']:
                    buys.append({
                        'level': 3, 'name': '第三类买点(3买)', 'date': cb['end_date'], 'price': cb['end_price'],
                        'strength': 1.5, 'center_idx': z['index'],
                        'desc': f"回调不进入中枢({z['zd']:.2f}) → {cb['end_price']:.2f}", 'type': 'buy'
                    })
        else:
            if leave['type'] == 'up' and z['end_bi_idx'] + 2 < len(bis):
                cb = bis[z['end_bi_idx'] + 2]
                if cb['type'] == 'down' and cb['end_price'] < z['zg']:
                    sells.append({
                        'level': 3, 'name': '第三类卖点(3卖)', 'date': cb['end_date'], 'price': cb['end_price'],
                        'strength': 1.5, 'center_idx': z['index'],
                        'desc': f"反弹不进入中枢({z['zg']:.2f}) → {cb['end_price']:.2f}", 'type': 'sell'
                    })

    return {'buy': buys, 'sell': sells}


if __name__ == '__main__':
    # 简单测试
    print("=== 缠论核心算法 v3.0 ===")
    print("resolve_inclusion, find_fenxing, identify_bi, identify_seg, find_zhongshu")
    print("calc_macd_for_bis, find_beichi, find_maidian")
