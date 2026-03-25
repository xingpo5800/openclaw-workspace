#!/usr/bin/env python3
"""
修复版东方财富历史数据测试 - 测试多只股票
"""

import requests
import pandas as pd
from datetime import datetime

def test_stock_historical(symbol, name, market=0):
    """测试单只股票的历史数据"""
    try:
        print(f"📈 测试{name}({symbol})历史数据...")
        
        url = "https://push2.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'secid': f'{market}.{symbol}',  # 0表示深圳，1表示上海
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日线
            'fqt': '1',
            'end': '20500101',
            'lmt': '120'  # 获取120天数据
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('data', {}).get('klines'):
                    klines = data['data']['klines']
                    print(f"✅ {name} 成功获取 {len(klines)} 条历史数据")
                    
                    # 转换为DataFrame
                    rows = []
                    for line in klines:
                        parts = line.split(',')
                        if len(parts) >= 12:
                            row = {
                                '日期': parts[0],
                                '开盘': float(parts[1]),
                                '收盘': float(parts[2]),
                                '最高': float(parts[3]),
                                '最低': float(parts[4]),
                                '成交量': int(parts[5]),
                                '成交额': float(parts[6]),
                                '振幅': float(parts[7]),
                                '涨跌幅': float(parts[8]),
                                '涨跌额': float(parts[9]),
                                '换手率': float(parts[10])
                            }
                            rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    print(f"📋 {name} 最近5天数据:")
                    print(df.tail()[['日期', '开盘', '收盘', '最高', '最低', '成交量']])
                    
                    return True, df
                else:
                    print(f"⚠️ {name} API返回数据格式异常")
                    return False, None
            except Exception as e:
                print(f"❌ {name} JSON解析失败: {e}")
                return False, None
        else:
            print(f"❌ {name} API请求失败: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ {name} 测试失败: {e}")
        return False, None

def main():
    """主函数"""
    print("🚀 开始测试多只股票的历史数据...")
    print("=" * 50)
    
    # 测试股票列表
    stocks = [
        ('000001', '平安银行', 0),    # 深圳A股
        ('000002', '万科A', 0),       # 深圳A股
        ('600000', '浦发银行', 1),   # 上海A股
        ('600036', '招商银行', 1),   # 上海A股
    ]
    
    results = []
    
    for symbol, name, market in stocks:
        success, df = test_stock_historical(symbol, name, market)
        results.append(success)
        
        if success and df is not None:
            # 保存数据到CSV
            filename = f"{symbol}_{name}_historical.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 {name} 数据已保存到 {filename}")
        
        print("-" * 30)
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试结果总结:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if any(results):
        print("🎉 至少有一只股票的历史数据获取成功！")
    else:
        print("⚠️ 所有股票的历史数据获取失败")

if __name__ == "__main__":
    main()