#!/usr/bin/env python3
"""
修复版东方财富历史数据测试
"""

import requests
import pandas as pd
from datetime import datetime

def test_eastmoney_historical_fixed():
    """测试东方财富历史数据（修复版）"""
    try:
        print("📈 测试东方财富历史数据（修复版）...")
        
        # 万科A的历史数据（深圳A股）
        symbol = "000001"
        url = "https://push2.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'secid': f'0.{symbol}',  # 0表示深圳，1表示上海
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
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📦 API返回数据结构: {list(data.keys())}")
                
                if data.get('data', {}).get('klines'):
                    klines = data['data']['klines']
                    print(f"✅ 成功获取 {len(klines)} 条历史数据")
                    
                    # 解析第一条数据看看格式
                    print(f"📋 数据格式示例: {klines[0]}")
                    
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
                    print("\n📋 最近5天数据:")
                    print(df.tail()[['日期', '开盘', '收盘', '最高', '最低', '成交量']])
                    
                    return True
                else:
                    print("⚠️ API返回数据格式异常")
                    print(f"📦 完整返回: {data}")
                    return False
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_eastmoney_historical_fixed()