#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5日均量上穿60日均量扫描器 v1.2

功能：
1. 扫描追踪池
2. 扫描量比排行榜Top100
3. 找出5日均量正在上穿60日均量的股票
4. 保存历史记录到CSV

使用方法：
python3 scan_volume_cross.py
"""

import requests
import json
import os


def get_stock_data(stock_code):
    """获取股票数据"""
    try:
        sym = 'sz' + stock_code if not stock_code.startswith('6') else 'sh' + stock_code
        r = requests.get(
            'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData',
            params={'symbol': sym, 'scale': '240', 'ma': 'no', 'datalen': 100},
            timeout=10
        )
        raw = r.json()
        if not raw or len(raw) < 65:
            return None

        vols = []
        closes = []
        for b in raw:
            v = b.get('volume')
            if v is None:
                continue
            vols.append(int(float(v)))
            closes.append(float(b['close']))

        if len(vols) < 65 or len(closes) < 65:
            return None

        avg_5 = sum(vols[-5:]) / 5
        avg_60 = sum(vols[-60:]) / 60
        avg_5_prev = sum(vols[-10:-5]) / 5

        ratio = avg_5 / avg_60 if avg_60 > 0 else 0
        slope_5 = (avg_5 - avg_5_prev) / avg_5_prev * 100 if avg_5_prev > 0 else 0

        # RSI
        c = closes[-14:]
        deltas = []
        for j in range(1, len(c)):
            deltas.append(c[j] - c[j - 1])
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]
        ag = sum(gains) / 14 if gains else 0
        al = sum(losses) / 14 if losses else 0
        rsi = 100 - (100 / (1 + ag / al)) if al else 50

        # 20日涨幅
        pct_20 = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) >= 21 else 0

        # 当日涨幅
        pct_today = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0

        return {
            'ratio': ratio,
            'slope_5': slope_5,
            'rsi': rsi,
            'pct_20': pct_20,
            'pct_today': pct_today,
            'price': closes[-1],
            'sym': sym
        }
    except:
        return None


def get_hot_stocks(limit=100):
    """获取量比排行榜"""
    try:
        r = requests.get(
            'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount',
            params={'node': 'hs_a'},
            timeout=10
        )
        return []
    except:
        return []


def get_top_volume(limit=200):
    """获取今日量比最高的股票（排除ST和北交所）"""
    try:
        # 获取涨幅榜（量大的机会多）
        r = requests.get(
            'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData',
            params={
                'page': 1,
                'num': limit * 2,  # 多取一些，过滤后够用
                'sort': 'volume',
                'asc': 0,
                'node': 'hs_a'
            },
            timeout=15
        )
        raw = r.json()
        stocks = []
        for item in raw:
            name = item.get('name', '')
            code = item.get('symbol', '').replace('sz', '').replace('sh', '')
            
            # 排除ST股票
            if 'ST' in name or '*ST' in name or 'S*ST' in name:
                continue
            
            # 排除北交所（代码以8或4开头，上海4开头，深圳8开头需要额外判断）
            # 北交所代码格式：bjxxxxx
            if item.get('symbol', '').startswith('bj'):
                continue
            
            stocks.append({
                'code': code,
                'name': name,
                'price': float(item.get('trade', 0)),
                'pct': float(item.get('pricechange', 0)) / float(item.get('settlement', 1)) * 100 if item.get('settlement') and float(item.get('settlement')) > 0 else 0
            })
            
            if len(stocks) >= limit:
                break
        
        return stocks
    except Exception as e:
        return []


def scan_stocks(stocks, name='未知'):
    """扫描股票列表"""
    results = []
    for stock in stocks:
        code = stock['code']
        data = get_stock_data(code)
        if not data:
            continue

        ratio = data['ratio']
        slope = data['slope_5']

        # 信号判断（放宽条件）
        signal = None
        if ratio >= 0.98 and slope > 0:
            signal = '上穿'
        elif slope > 30:
            signal = '量增'  # 量能明显增加

        if signal:
            results.append({
                'code': code,
                'name': stock.get('name', code),
                'ratio': ratio,
                'slope': slope,
                'rsi': data['rsi'],
                'pct_20': data['pct_20'],
                'pct_today': data['pct_today'],
                'price': data['price'],
                'signal': signal
            })

    return results


def main():
    print('=' * 70)
    print('5日均量上穿60日均量扫描器 v1.1')
    print('=' * 70)

    all_results = []

    # 1. 扫描追踪池
    pf_path = os.path.join(os.path.dirname(__file__), 'portfolio.json')
    if os.path.exists(pf_path):
        with open(pf_path) as f:
            stocks = json.load(f)
        active = [s for s in stocks.values() if not s.get('hidden')]
        print(f'\n【扫描追踪池】{len(active)} 只')

        pool_results = []
        for code, info in stocks.items():
            if info.get('hidden'):
                continue
            stock = {'code': code, 'name': info.get('name', code)}
            data = get_stock_data(code)
            if not data:
                continue

            ratio = data['ratio']
            slope = data['slope_5']

            signal = None
            if ratio >= 0.98 and slope > 0:
                signal = '上穿'
            elif slope > 30:
                signal = '量增'

            if signal:
                pool_results.append({
                    'code': code,
                    'name': info.get('name', code),
                    'ratio': ratio,
                    'slope': slope,
                    'rsi': data['rsi'],
                    'pct_20': data['pct_20'],
                    'pct_today': data['pct_today'],
                    'price': data['price'],
                    'signal': signal
                })
                all_results.append(pool_results[-1])

        if pool_results:
            pool_results.sort(key=lambda x: x['ratio'], reverse=True)
            for r in pool_results:
                slope_ok = 'V' if r['slope'] > 30 else ' '
                rsi_ok = 'V' if r['rsi'] < 52 else ' '
                print(f"  {r['name']:<10} {r['code']} 量比:{r['ratio']:.2f}x "
                      f"斜率:{r['slope']:>+6.1f}%{slope_ok} RSI:{r['rsi']:5.1f}{rsi_ok} "
                      f"今日:{r['pct_today']:>+5.1f}% 20日:{r['pct_20']:>+6.1f}% [{r['signal']}]")
        else:
            print('  暂无信号')

    # 2. 扫描量比榜Top100
    print(f'\n【扫描量比榜Top100】')
    hot_stocks = get_top_volume(100)
    if hot_stocks:
        print(f'  获取到 {len(hot_stocks)} 只股票...')
        hot_results = scan_stocks(hot_stocks[:50], '量比榜')
        all_results.extend(hot_results)

        if hot_results:
            hot_results.sort(key=lambda x: x['ratio'], reverse=True)
            for r in hot_results[:10]:
                slope_ok = 'V' if r['slope'] > 30 else ' '
                rsi_ok = 'V' if r['rsi'] < 52 else ' '
                print(f"  {r['name']:<10} {r['code']} 量比:{r['ratio']:.2f}x "
                      f"斜率:{r['slope']:>+6.1f}%{slope_ok} RSI:{r['rsi']:5.1f}{rsi_ok} "
                      f"今日:{r['pct_today']:>+5.1f}% 20日:{r['pct_20']:>+6.1f}% [{r['signal']}]")
        else:
            print('  暂无信号')

    # 汇总
    if all_results:
        print('\n' + '=' * 70)
        print('【量增信号】5日均量线向上 + 斜率>30')
        print('-' * 70)

        best = [r for r in all_results if r['signal'] == '量增']
        best.sort(key=lambda x: x['rsi'])  # RSI低的优先

        if best:
            for r in best[:20]:
                rsi_ok = 'V' if r['rsi'] < 52 else ' '
                print(f"  {r['name']:<10} {r['code']} 量比:{r['ratio']:.2f}x "
                      f"斜率:{r['slope']:>+6.1f}% RSI:{r['rsi']:5.1f}{rsi_ok} "
                      f"今日:{r['pct_today']:>+5.1f}% 20日:{r['pct_20']:>+6.1f}%")
        else:
            print('  暂无符合条件的股票')

        print('\n【上穿成功观察】5日均量已上穿60日均量 + 斜率>30')
        print('-' * 70)
        observe = [r for r in all_results if r['signal'] == '上穿']
        observe.sort(key=lambda x: x['rsi'])  # RSI低的优先
        if observe:
            for r in observe[:20]:
                rsi_ok = 'V' if r['rsi'] < 52 else ' '
                print(f"  {r['name']:<10} {r['code']} 量比:{r['ratio']:.2f}x "
                      f"斜率:{r['slope']:>+6.1f}% RSI:{r['rsi']:5.1f}{rsi_ok} "
                      f"今日:{r['pct_today']:>+5.1f}% 20日:{r['pct_20']:>+6.1f}%")
        else:
            print('  暂无符合条件的股票')

    print('\n' + '=' * 70)

    # 保存历史记录
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    csv_path = os.path.join(os.path.dirname(__file__), 'scan_history.csv')
    with open(csv_path, 'a') as f:
        for r in all_results:
            f.write(f"{today},{r['code']},{r['name']},{r['signal']},{r['ratio']:.2f},{r['slope']:+.1f},{r['rsi']:.1f},{r['pct_20']:+.1f},{r['pct_today']:+.1f},pending\n")


if __name__ == '__main__':
    main()
