#!/usr/bin/env python3
"""
缠论中枢、背驰、三类买卖点模块 v3.0
核心算法已迁移到 chan_core.py (v3.0，基于全书完整理解重写)
功能：
  - 中枢识别（Chan.zhongshu）
  - 背驰判断（Chan.beichi）
  - 三类买卖点（Chan.maidian）
  - 综合评分（Chan.score）

用法：
  python3 chan.py 002929              # 分析润建股份
  python3 chan.py 002929 --days 120  # 分析最近120天
  python3 chan.py 002929 --raw        # 显示原始K线
"""

import requests
import sys
import json
from datetime import datetime

# 从 chan_core 导入 v3.0 核心算法
from chan_core import (
    resolve_inclusion, find_fenxing, identify_bi, identify_seg,
    find_zhongshu, calc_macd_for_bis, find_beichi, find_maidian,
    calc_ema as _calc_ema
)

DEFAULT_MIN_BARS = 3  # 笔识别的最小K线数（缠论标准=5，实盘用3否则数据太少）

# ========== 新浪财经API（兼容日K/分钟K）==========
def get_kline(secid, days=120):
    """获取日K线 - 使用新浪财经API，兼容股票和指数"""
    # secid格式: 1.000001(上证) 或 0.000001(深证)
    # 特殊处理：指数用sh/sz前缀，股票用sz/sh前缀
    code = secid.split('.')[1] if '.' in secid else secid
    
    # 上证指数特殊处理
    if code in ('000001', '000300', '000016', '000688') or secid.startswith('1.'):
        symbol = f"sh{code}"
    else:
        symbol = f"sz{code}" if not code.startswith(('sh', 'sz')) else f"{code}"
    
    # 新浪日K API: scale=240 表示日线
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    params = {
        'symbol': symbol,
        'scale': '240',
        'ma': 'no',
        'datalen': min(days, 5000)
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        raw = r.json()
        if not raw or not isinstance(raw, list):
            # 降级：尝试腾讯ifzq API
            return _get_kline_ifzq(secid, days)
        result = []
        for bar in raw:
            try:
                result.append({
                    'date': bar['day'],
                    'open': float(bar['open']),
                    'close': float(bar['close']),
                    'high': float(bar['high']),
                    'low': float(bar['low']),
                    'volume': int(float(bar.get('volume', 0)))
                })
            except (ValueError, KeyError):
                continue
        # 按日期升序排序
        result.sort(key=lambda x: x['date'])
        return result
    except Exception as e:
        print(f"  Sina API失败: {e}，尝试降级...")
        return _get_kline_ifzq(secid, days)

def _get_kline_ifzq(secid, days=120):
    """腾讯ifzq降级接口"""
    market = 'sh' if secid.startswith('1.') else 'sz'
    code = secid.split('.')[1] if '.' in secid else secid
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {
        '_var': 'kline_dayhfq',
        'param': f"{market}{code},day,2020-01-01,2050-12-31,{days},qfq"
    }
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
        raw = d.get(f"{market}{code}", {}).get('qfqday', d.get(f"{market}{code}", {}).get('day', []))
        result = []
        for line in raw:
            if len(line) >= 6:
                try:
                    result.append({
                        'date': line[0], 'open': float(line[1]), 'close': float(line[2]),
                        'high': float(line[3]), 'low': float(line[4]), 'volume': int(float(line[5]))
                    })
                except (ValueError, IndexError):
                    continue
        result.sort(key=lambda x: x['date'])
        return result
    except Exception:
        return []

def secid_of(symbol):
    """股票代码 → secid格式"""
    s = symbol.strip()
    if s.startswith(('6', '5', '9', '7', '0', '3')) and len(s) == 6:
        if s.startswith(('6', '5', '9', '7')):
            return f"1.{s}"
        return f"0.{s}"
    return symbol


# 核心算法已迁移到 chan_core.py（v3.0，基于全书完整理解）


# ========== 综合评分 ==========
def calc_comprehensive_score(bis, zhongshu_list, beichi_signals, maidian, resolved_klines):
    """
    综合评分（缠论 + RSI + MACD）满分10分
    - 缠论买点  最高3分
    - RSI      最高2分
    - MACD     最高2分
    - 中枢位置  最高2分
    - 趋势方向  最高1分
    """
    if not resolved_klines or len(resolved_klines) < 20:
        return {'score': 0, 'detail': {}, 'recommendation': '数据不足'}
    closes = [k['close'] for k in resolved_klines]
    latest_close = closes[-1]

    # RSI
    def calc_rsi14(closes):
        if len(closes) < 15:
            return 50
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains.append(max(d, 0)); losses.append(max(-d, 0))
        ag = sum(gains[-14:]) / 14
        al = sum(losses[-14:]) / 14
        if al == 0: return 100
        return 100 - (100 / (1 + ag / al))
    rsi = calc_rsi14(closes)

    # MACD
    ema12 = _calc_ema(closes, 12)
    ema26 = _calc_ema(closes, 26)
    dif = ema12[-1] - ema26[-1]
    dif_arr = [ema12[i] - ema26[i] for i in range(len(closes))]
    dea = _calc_ema(dif_arr, 9)[-1]
    macd_hist = 2 * (dif - dea)

    # 趋势
    recent = bis[-4:] if len(bis) >= 4 else bis
    up_cnt = sum(1 for b in recent if b['type'] == 'up')
    down_cnt = len(recent) - up_cnt
    trend = 'up' if up_cnt > down_cnt else ('down' if down_cnt > up_cnt else 'neutral')

    detail = {}
    total = 0.0

    # 1. 缠论买点（3分）
    buys = maidian.get('buy', [])
    if buys:
        # 取最强且最近的买点
        buys_sorted = sorted(buys, key=lambda x: -x['strength'])
        best = buys_sorted[0]
        level_mult = {1: 1.0, 2: 0.7, 3: 0.5}
        chan_score = min(best['strength'] * level_mult.get(best['level'], 0.5), 3.0)
        detail['缠论买点'] = f"{best['name']} 强度{best['strength']}分"
    else:
        chan_score = 0
        detail['缠论买点'] = '无明显买点'
    total += chan_score

    # 2. RSI（2分）
    if rsi < 30:
        rsi_score = 2.0; detail['RSI'] = f"{rsi:.0f} 严重超卖 ✅"
    elif rsi < 40:
        rsi_score = 1.5; detail['RSI'] = f"{rsi:.0f} 偏弱超卖 ✅"
    elif 40 <= rsi <= 60:
        rsi_score = 1.0; detail['RSI'] = f"{rsi:.0f} 中性区间"
    elif 60 < rsi <= 70:
        rsi_score = 0.5; detail['RSI'] = f"{rsi:.0f} 偏强"
    else:
        rsi_score = 0.0; detail['RSI'] = f"{rsi:.0f} 超买 ⚠️"
    total += rsi_score

    # 3. MACD（2分）
    if dif > 0 and macd_hist > 0:
        macd_score = 2.0; detail['MACD'] = '多头状态 ✅'
    elif dif > 0 and -0.5 < macd_hist < 0:
        macd_score = 1.5; detail['MACD'] = '接近金叉 ✅'
    elif dif < 0 and macd_hist < 0:
        macd_score = 0.5; detail['MACD'] = '空头状态 ⚠️'
    else:
        macd_score = 1.0; detail['MACD'] = '整理中'
    total += macd_score

    # 4. 中枢位置（2分）
    if zhongshu_list and resolved_klines:
        latest_z = zhongshu_list[-1]
        if latest_z['type'] == 'up':
            if latest_close > latest_z['zg']:
                center_score = 2.0; detail['中枢位置'] = f"价格在ZG{latest_z['zg']:.2f}上方，多头 ✅"
            elif latest_close > latest_z['zd']:
                center_score = 1.0; detail['中枢位置'] = f"价格在中枢内震荡"
            else:
                center_score = 0.0; detail['中枢位置'] = f"价格在ZD{latest_z['zd']:.2f}下方，空头 ⚠️"
        else:
            # down类型：zd是更高值（中枢上沿），zg是更低值（中枢下沿）
            if latest_close > latest_z['zd']:
                center_score = 2.0; detail['中枢位置'] = f"价格在ZD{latest_z['zd']:.2f}上方，多头 ✅"
            elif latest_close > latest_z['zg']:
                center_score = 1.0; detail['中枢位置'] = f"价格在中枢内震荡"
            else:
                center_score = 0.0; detail['中枢位置'] = f"价格在ZG{latest_z['zg']:.2f}下方，空头 ⚠️"
    else:
        center_score = 1.0; detail['中枢位置'] = '无中枢信号'
    total += center_score

    # 5. 趋势（1分）
    if trend == 'up':
        trend_score = 1.0; detail['趋势'] = '上升趋势 ✅'
    elif trend == 'down':
        trend_score = 0.0; detail['趋势'] = '下降趋势 ⚠️'
    else:
        trend_score = 0.5; detail['趋势'] = '震荡整理'
    total += trend_score

    # 建议
    score = round(total, 1)
    if score >= 7.5:
        recommendation = '强烈买入'
    elif score >= 6.0:
        recommendation = '建议买入'
    elif score >= 4.5:
        recommendation = '谨慎关注'
    elif score >= 3.0:
        recommendation = '建议观望'
    else:
        recommendation = '建议卖出/空仓'

    return {
        'score': score, 'max': 10.0,
        'detail': detail,
        'recommendation': recommendation,
        'rsi': round(rsi, 1),
        'macd_hist': round(macd_hist, 3),
        'dif': round(dif, 3),
        'trend': trend,
    }


# ========== 可视化 & 展示 ==========
def print_zhongshu(zhongshu_list):
    """打印中枢列表"""
    if not zhongshu_list:
        print("  （未识别到中枢）")
        return
    print(f"\n🏛️  中枢识别结果（共 {len(zhongshu_list)} 个）")
    print(f"{'='*85}")
    print(f"{'编号':<4} {'起始日期':<12} {'结束日期':<12} {'上轨ZG':>8} {'下轨ZD':>8} {'宽度%':>7}")
    print(f"{'-'*85}")
    for z in zhongshu_list:
        print(f"{z['index']:<4} {z['start_date']:<12} {z['end_date']:<12} "
              f"{z['zg']:>8.2f} {z['zd']:>8.2f} {z['range_width']:>6.2f}%")

def print_beichi(beichi_signals):
    """打印背驰信号"""
    if not beichi_signals:
        print("  （未识别到背驰）")
        return
    print(f"\n⚡ 背驰信号（共 {len(beichi_signals)} 个）")
    print(f"{'='*85}")
    print(f"{'类型':<8} {'日期':<12} {'前价格':>8} {'后价格':>8} {'力度比':>7} {'强度':>5} {'中枢#':>5} {'描述'}")
    print(f"{'-'*85}")
    for bc in beichi_signals:
        icon = '🔴顶背驰' if bc['type'] == '顶背驰' else '🟢底背驰'
        print(f"{icon:<10} {bc['date']:<12} {bc['price_before']:>8.2f} {bc['price_after']:>8.2f} "
              f"{bc['bei_ratio']:>7.1f}x {bc['strength']:>5.1f} 中枢{bc['center_idx']:<3} {bc['desc']}")

def print_maidian(maidian):
    """打印买卖点"""
    buys = maidian.get('buy', [])
    sells = maidian.get('sell', [])
    print(f"\n🎯 三类买卖点")
    print(f"{'='*85}")
    if not buys and not sells:
        print("  （未识别到买卖点）")
        return
    if buys:
        print(f"  【买点】")
        for b in buys:
            icon = {1: '🥇', 2: '🥈', 3: '🥉'}.get(b['level'], '•')
            print(f"    {icon} {b['name']} | 日期:{b['date']} | 价格:{b['price']:.2f} | 强度:{b['strength']} | {b['desc']}")
    if sells:
        print(f"  【卖点】")
        for s in sells:
            icon = {1: '🥇', 2: '🥈', 3: '🥉'}.get(s['level'], '•')
            print(f"    {icon} {s['name']} | 日期:{s['date']} | 价格:{s['price']:.2f} | 强度:{s['strength']} | {s['desc']}")

def print_score(score_result):
    """打印综合评分"""
    r = score_result
    if r.get('recommendation') == '数据不足':
        print("\n  （数据不足，无法评分）")
        return
    print(f"\n📊 综合评分: {r['score']:.1f}/10  →  {r['recommendation']}  {'✅' if r['score'] >= 6 else '⚠️' if r['score'] >= 4 else '🔴'}")
    print(f"  {'='*50}")
    for k, v in r.get('detail', {}).items():
        print(f"  {k:<10} {v}")
    print(f"  {'-'*50}")
    print(f"  RSI={r.get('rsi',0):.0f}  MACD柱={r.get('macd_hist',0):.2f}  趋势={r.get('trend','?')}")

def print_bis(bis, resolved_klines=None):
    """打印笔列表"""
    if not bis:
        print("  （未识别到笔）")
        return
    up_count = sum(1 for b in bis if b['type'] == 'up')
    down_count = sum(1 for b in bis if b['type'] == 'down')
    print(f"\n📊 笔识别结果（共 {len(bis)} 笔 | ↑上升{up_count}笔 ↓下降{down_count}笔）")
    print(f"{'='*80}")
    print(f"{'类型':<4} {'起始日期':<12} {'结束日期':<12} {'起始价':>8} {'结束价':>8} {'幅度':>7} {'K线数':>5}")
    print(f"{'-'*80}")
    for bi in bis:
        arrow = '↑' if bi['type'] == 'up' else '↓'
        color_tag = '🟢' if bi['type'] == 'up' else '🔴'
        print(f"{color_tag}{arrow:<2} {bi['start_date']:<12} {bi['end_date']:<12} "
              f"{bi['start_price']:>8.2f} {bi['end_price']:>8.2f} {bi['amplitude']:>+6.1f}% {bi['bars_count']:>4d}")


def print_segs(segs):
    """打印线段列表"""
    if not segs:
        print("\n  （未识别到线段，需3个以上同方向笔）")
        return
    print(f"\n📊 线段识别结果（共 {len(segs)} 段）")
    print(f"{'='*80}")
    print(f"{'类型':<4} {'起始日期':<12} {'结束日期':<12} {'起始价':>8} {'结束价':>8} {'幅度':>7} {'笔数':>4}")
    print(f"{'-'*80}")
    for seg in segs:
        arrow = '↑' if seg['type'] == 'up' else '↓'
        color_tag = '🟢' if seg['type'] == 'up' else '🔴'
        print(f"{color_tag}{arrow:<2} {seg['start_date']:<12} {seg['end_date']:<12} "
              f"{seg['start_price']:>8.2f} {seg['end_price']:>8.2f} {seg['amplitude']:>+6.1f}% {seg['bi_count']:>4d}")


def print_klines_comparison(klines, resolved, max_show=40):
    """打印原始K线与处理后K线对比"""
    print(f"\n📋 K线包含处理对比（显示最近{max_show}根）")
    n = min(len(klines), len(resolved), max_show)
    print(f"{'-'*80}")
    print(f"{'日期':<12} {'原始-开':>7} {'原始-高':>7} {'原始-低':>7} {'原始-收':>7} | {'处理-高':>7} {'处理-低':>7}")
    print(f"{'-'*80}")
    for i in range(n):
        k = klines[-(n - i)]
        r = resolved[-(min(n, len(resolved)) - i)] if i < len(resolved) else k
        changed = " *变更*" if (r['high'] != k['high'] or r['low'] != k['low']) else ""
        print(f"{k['date']:<12} {k['open']:>7.2f} {k['high']:>7.2f} {k['low']:>7.2f} {k['close']:>7.2f} | "
              f"{r['high']:>7.2f} {r['low']:>7.2f}{changed}")


def print_statistics(bis, segs):
    """打印统计摘要"""
    if not bis:
        return
    ups = [b for b in bis if b['type'] == 'up']
    downs = [b for b in bis if b['type'] == 'down']
    print(f"\n📈 统计摘要")
    print(f"  笔总数: {len(bis)}（↑{len(ups)}笔 ↓{len(downs)}笔）")
    if ups:
        avg_up = sum(b['amplitude'] for b in ups) / len(ups)
        print(f"  上升笔平均幅度: {avg_up:+.2f}%")
    if downs:
        avg_down = sum(b['amplitude'] for b in downs) / len(downs)
        print(f"  下降笔平均幅度: {avg_down:+.2f}%")
    if segs:
        print(f"  线段总数: {len(segs)}")
        max_up = max((s for s in segs if s['type']=='up'), key=lambda s: s['amplitude'], default=None)
        max_down = max((s for s in segs if s['type']=='down'), key=lambda s: s['amplitude'], default=None)
        if max_up:
            print(f"  最大上升线段: {max_up['amplitude']:+.1f}% ({max_up['start_date']}→{max_up['end_date']})")
        if max_down:
            print(f"  最大下降线段: {max_down['amplitude']:+.1f}% ({max_down['start_date']}→{max_down['end_date']})")


# ========== 主分析函数 ==========
def analyze(symbol, days=120, show_raw=False):
    """完整缠论分析（笔段+中枢+背驰+买卖点+综合评分）"""
    secid = secid_of(symbol)
    print(f"\n{'='*80}")
    print(f"🌀 缠论完整分析  股票代码: {symbol}  分析天数: {days}天")
    print(f"{'='*80}")

    klines = get_kline(secid, days)
    if not klines:
        print("❌ 数据获取失败")
        return None

    print(f"✅ 获取K线 {len(klines)} 根（{klines[0]['date']} → {klines[-1]['date']}）")

    # Step 1: 处理包含关系
    resolved = resolve_inclusion(klines)
    print(f"📐 包含处理后：{len(klines)} → {len(resolved)} 根（去除 {len(klines) - len(resolved)} 组包含关系）")

    if show_raw:
        print_klines_comparison(klines, resolved)

    # Step 2: 分型识别
    fenxings = find_fenxing(resolved)
    tops = [f for f in fenxings if f['type'] == 'top']
    bottoms = [f for f in fenxings if f['type'] == 'bottom']
    print(f"\n🔺 分型识别：共 {len(fenxings)} 个（△顶分型 {len(tops)} 个 ▽底分型 {len(bottoms)} 个）")

    # Step 3: 笔识别（v3.0：传入resolve后的K线）
    bis = identify_bi(resolved, DEFAULT_MIN_BARS)
    print_bis(bis, resolved)

    # Step 4: 线段识别
    segs = identify_seg(bis)
    print_segs(segs)

    # Step 5: 中枢识别（核心新增）
    zhongshu_list = find_zhongshu(bis)
    print_zhongshu(zhongshu_list)

    # Step 6: MACD力度计算（基于resolved klines，与bi索引对齐）
    macd_data = calc_macd_for_bis(resolved, bis)

    # Step 7: 背驰判断
    beichi_signals = find_beichi(bis, zhongshu_list, macd_data)
    print_beichi(beichi_signals)

    # Step 8: 三类买卖点
    maidian = find_maidian(bis, zhongshu_list, beichi_signals)
    print_maidian(maidian)

    # Step 9: 综合评分（基于resolved klines）
    score_result = calc_comprehensive_score(bis, zhongshu_list, beichi_signals, maidian, resolved)
    print_score(score_result)

    # Step 10: 统计
    print_statistics(bis, segs)

    print(f"\n{'='*80}")
    print(f"✅ 缠论完整分析完成 | 笔数:{len(bis)} | 线段:{len(segs)} | 中枢:{len(zhongshu_list)} | 背驰:{len(beichi_signals)}")

    return {
        'klines': klines, 'resolved': resolved,
        'fenxings': fenxings, 'bis': bis, 'segs': segs,
        'zhongshu': zhongshu_list, 'macd_data': macd_data,
        'beichi': beichi_signals, 'maidian': maidian, 'score': score_result,
    }


# ========== 命令行入口 ==========
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    symbol = sys.argv[1]
    days = 120
    show_raw = False
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--days' and i + 1 < len(args):
            days = int(args[i + 1]); i += 2
        elif args[i] == '--raw':
            show_raw = True; i += 1
        else:
            i += 1
    result = analyze(symbol, days, show_raw)
    if result:
        print(f"\n{'='*80}")
        print(f"✅ 缠论分析完成 | 笔数:{len(result['bis'])} | 线段:{len(result['segs'])} | "
              f"中枢:{len(result['zhongshu'])} | 背驰:{len(result['beichi'])}")


# ========== 缠论 + RSI + MACD 综合打分 ==========
def calc_integrated_score(symbol, days=120, scale='240'):
    """
    缠论 + RSI + MACD 综合评分
    返回: {
        'rsi': float, 'macd': float, 'dif': float,
        'chan_signals': [...], 'score': 0-100,
        'recommendation': str,
        'entry_price': float, 'stop_loss': float
    }
    """
    import requests as req

    # 获取数据 - 使用get_kline（包含ifzq降级）
    _symbol = symbol.strip()
    # 处理 sh/sz 前缀
    if not _symbol.startswith(('sh', 'sz')):
        _symbol = secid_of(_symbol)
    klines = get_kline(_symbol, days)
    if len(klines) < 30:
        return {'error': '数据不足'}
    
    closes = [k['close'] for k in klines]
    
    # RSI
    deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains = [d for d in deltas[-14:] if d>0]
    losses = [-d for d in deltas[-14:] if d<0]
    ag = sum(gains)/14 if gains else 0
    al = sum(losses)/14 if losses else 0
    rsi = 100-(100/(1+ag/al)) if al else 100
    
    # MACD
    e12 = [closes[0]]; e26 = [closes[0]]
    for c in closes[1:]:
        e12.append(c*2/13+e12[-1]*11/13)
        e26.append(c*2/27+e26[-1]*25/27)
    dif = [e12[i]-e26[i] for i in range(len(closes))]
    dea = [dif[0]]
    for d in dif[1:]:
        dea.append(d*2/10+dea[-1]*8/10)
    macd = [2*(dif[i]-dea[i]) for i in range(len(closes))]
    
    # 缠论
    resolved = resolve_inclusion(klines)
    bis = identify_bi(resolved, DEFAULT_MIN_BARS)
    zs = find_zhongshu(bis)
    macd_data = calc_macd_for_bis(resolved, bis)
    beichi = find_beichi(bis, zs, macd_data)
    maidian = find_maidian(bis, zs, beichi)
    
    # ===== 综合打分 =====
    score = 0
    signals = []
    
    # 量价评分
    vol_score, vol_signals = calc_volume_price_score(klines)
    score += vol_score
    for s in vol_signals: signals.append(s)
    
    # 量价评分说明
    if vol_score > 0: signals.append(f'量价看多(+{vol_score})')
    elif vol_score < 0: signals.append(f'量价看空({vol_score})')
    
    # RSI 20分
    if rsi < 30: score += 20; signals.append(f'RSI超卖({rsi:.0f})')
    elif rsi < 40: score += 12; signals.append(f'RSI偏低({rsi:.0f})')
    elif rsi > 70: score -= 10; signals.append(f'RSI超买({rsi:.0f})')
    elif rsi > 60: score -= 5; signals.append(f'RSI偏高({rsi:.0f})')
    else: score += 5; signals.append(f'RSI中性({rsi:.0f})')
    
    # MACD 20分
    if macd[-1] > 0 and macd[-1] > macd[-2]: score += 20; signals.append('MACD多头')
    elif macd[-1] > 0: score += 10; signals.append('MACD偏多')
    elif macd[-1] < 0 and macd[-1] < macd[-2]: score -= 15; signals.append('MACD空头发散')
    elif macd[-1] < 0: score -= 5; signals.append('MACD空头收敛')
    else: score += 0; signals.append('MACD整理')
    
    # 缠论买点 30分
    buy_score = 0
    for m in maidian['buy']:
        if m['name'] == '第一类买点(1买)': buy_score = max(buy_score, 30)
        elif m['name'] == '第二类买点(2买)': buy_score = max(buy_score, 20)
        elif m['name'] == '第三类买点(3买)': buy_score = max(buy_score, 15)
    score += buy_score
    if buy_score > 0: signals.append(f'缠论{["无","一买","二买","三买"][buy_score//10]}')
    
    # 缠论卖点 -20分
    sell_score = 0
    for m in maidian['sell']:
        if m['name'] == '第一类卖点(1卖)': sell_score = max(sell_score, -20)
        elif m['name'] == '第二类卖点(2卖)': sell_score = max(sell_score, -15)
        elif m['name'] == '第三类卖点(3卖)': sell_score = max(sell_score, -10)
    score += sell_score
    
    # 背驰信号 ±10分
    for b in beichi:
        if '底' in b['type'] and b['bei_ratio'] > 1.3: score += 10; signals.append(f'底背驰({b["bei_ratio"]}x)'); break
        elif '顶' in b['type'] and b['bei_ratio'] > 1.3: score -= 10; signals.append(f'顶背驰({b["bei_ratio"]}x)'); break
    
    score = max(0, min(100, score))
    
    # 建议和关键价
    latest_close = closes[-1]
    if score >= 60: rec = '买入信号'; entry = latest_close; stop = latest_close * 0.95
    elif score >= 45: rec = '谨慎买入'; entry = latest_close; stop = latest_close * 0.93
    elif score >= 35: rec = '观望'; entry = None; stop = None
    else: rec = '不介入'; entry = None; stop = None
    
    return {
        'symbol': symbol, 'date': klines[-1]['date'],
        'close': latest_close,
        'rsi': round(rsi, 1), 'dif': round(dif[-1], 4), 'macd': round(macd[-1], 4),
        'chan': {'bis': len(bis), 'zs': len(zs), 'beichi': len(beichi), 'buy': len(maidian['buy']), 'sell': len(maidian['sell'])},
        'signals': signals, 'score': score,
        'recommendation': rec, 'entry_price': entry, 'stop_loss': stop
    }


def print_integrated(symbol, days=120, scale='240'):
    """综合分析打印"""
    result = calc_integrated_score(symbol, days, scale)
    if 'error' in result:
        print(f"❌ {result['error']}"); return
    
    print(f"\n{'='*50}")
    print(f"  综合评分系统 | {symbol} | {result['date']}")
    print(f"{'='*50}")
    print(f"  现价: {result['close']:.2f}")
    print(f"  RSI: {result['rsi']}  |  DIF: {result['dif']}  |  MACD: {result['macd']}")
    print(f"  缠论: {result['chan']['bis']}笔/{result['chan']['zs']}中枢/{result['chan']['beichi']}背驰 | 买{result['chan']['buy']}卖{result['chan']['sell']}")
    print()
    print(f"  信号:")
    for s in result['signals']:
        print(f"    ● {s}")
    print()
    print(f"  综合评分: {result['score']}/100  →  {result['recommendation']}")
    if result['entry_price']:
        print(f"  建议入场: {result['entry_price']:.2f}  |  止损: {result['stop_loss']:.2f}")
    print(f"{'='*50}\n")


# ========== 量价分析 ==========
def calc_volume_price_score(klines):
    """
    蜡烛图量价评分
    基于最近5根K线的量价关系
    返回: (score: -15~+15, signals: [str])
    """
    if len(klines) < 5:
        return 0, []
    
    closes = [k['close'] for k in klines]
    opens = [k['open'] for k in klines]
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    volumes = [k.get('volume', 0) for k in klines]
    
    # 平均成交量
    vol_avg = sum(volumes[-5:]) / 5
    
    score = 0
    signals = []
    
    # 最后一根K线
    last = klines[-1]
    body = abs(last['close'] - last['open'])
    upper_shadow = last['high'] - max(last['close'], last['open'])
    lower_shadow = min(last['close'], last['open']) - last['low']
    is_bullish = last['close'] > last['open']
    vol_ratio = last.get('volume', 0) / vol_avg if vol_avg > 0 else 1
    
    # 锤子线（下影线长，底部信号）
    if lower_shadow > body * 2 and body > 0 and lower_shadow > upper_shadow:
        score += 10
        signals.append(f'锤子线(下影>{body*2:.1f})')
    
    # 射击之星（上影线长，顶部信号）
    if upper_shadow > body * 2 and body > 0 and upper_shadow > lower_shadow:
        score -= 10
        signals.append(f'射击之星(上影>{body*2:.1f})')
    
    # 吞没形态（阳包阴/阴包阳）
    if len(klines) >= 2:
        prev = klines[-2]
        prev_body = abs(prev['close'] - prev['open'])
        body1 = abs(last['close'] - last['open'])
        if prev_body > 0 and body1 > 0:
            # 阳包阴（底部买入信号）
            if prev['close'] < prev['open'] and last['close'] > last['open'] and last['close'] > prev['open'] and last['open'] < prev['close']:
                score += 8
                signals.append('阳包阴(买入)')
            # 阴包阳（顶部卖出信号）
            elif prev['close'] > prev['open'] and last['close'] < last['open'] and last['close'] < prev['open'] and last['open'] > prev['close']:
                score -= 8
                signals.append('阴包阳(卖出)')
    
    # 量价配合
    today_chg = (last['close'] - closes[-2]) / closes[-2] if closes[-2] > 0 else 0
    if today_chg > 0.02 and vol_ratio > 1.3:  # 价涨量增
        score += 5
        signals.append(f'价涨量增({vol_ratio:.1f}x)')
    elif today_chg > 0.02 and vol_ratio < 0.7:  # 价涨量缩
        score -= 3
        signals.append(f'价涨量缩({vol_ratio:.1f}x)')
    elif today_chg < -0.02 and vol_ratio > 1.3:  # 价跌量增
        score -= 5
        signals.append(f'价跌量增({vol_ratio:.1f}x)')
    elif today_chg < -0.02 and vol_ratio < 0.7:  # 价跌量缩
        score += 3
        signals.append(f'价跌量缩({vol_ratio:.1f}x)')
    
    # 底部放量
    if vol_ratio > 2.0 and last['close'] < sum(closes[-5:]) / 5:
        score += 5
        signals.append(f'底部放量({vol_ratio:.1f}x)')
    
    # 顶部放量
    if vol_ratio > 2.0 and last['close'] > sum(closes[-5:]) / 5:
        score -= 5
        signals.append(f'顶部放量({vol_ratio:.1f}x)')
    
    # 限制范围
    score = max(-15, min(15, score))
    
    return score, signals


