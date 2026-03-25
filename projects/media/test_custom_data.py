#!/usr/bin/env python3
"""
修改版AKShare测试脚本
跳过curl_cffi依赖，使用requests替代
"""

import sys
import os
import requests
import pandas as pd
from datetime import datetime

# 添加AKShare源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'akshare'))

def test_eastmoney_realtime():
    """测试东方财富实时行情数据"""
    try:
        print("📈 测试东方财富实时行情数据...")
        
        # 东方财富实时行情API
        url = "https://80.push2.eastmoney.com/api/qt/clist/get"
        params = {
            'fid': 'f62',  # 涨跌幅
            'po': '1',     # 排序方式
            'pz': '20',    # 每页数量
            'pn': '1',     # 页码
            'np': '1',
            'fltt': '2',
            'invt': '2',
            'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # 沪深A股
            'fields': 'f12,f14,f2,f3,f5,f6,f15,f20,f21,f62,f127,f128,f152,f184',
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
                if data.get('data', {}).get('diff'):
                    stocks = data['data']['diff']
                    print(f"✅ 成功获取 {len(stocks)} 只股票数据")
                    
                    # 显示前5只股票
                    print("\n📋 前5只股票信息:")
                    for i, stock in enumerate(stocks[:5]):
                        print(f"{i+1}. {stock.get('f12', 'N/A')} - {stock.get('f14', 'N/A')}: "
                              f"最新价={stock.get('f2', 'N/A')}, 涨跌幅={stock.get('f62', 'N/A')}%")
                    
                    return True
                else:
                    print("⚠️ API返回数据格式异常")
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

def test_eastmoney_historical():
    """测试东方财富历史数据"""
    try:
        print("\n📈 测试东方财富历史数据...")
        
        # 万科A的历史数据
        symbol = "000001"
        url = "https://push2.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'secid': f'1.{symbol}',  # 1表示上海，0表示深圳
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
                if data.get('data', {}).get('klines'):
                    klines = data['data']['klines']
                    print(f"✅ 成功获取 {len(klines)} 条历史数据")
                    
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

def test_tencent_realtime():
    """测试腾讯财经实时行情数据"""
    try:
        print("\n📈 测试腾讯财经实时行情数据...")
        
        url = "https://qt.gtimg.cn/q="
        params = {
            'q': 'sh000001,sz000001',  # 上证指数和万科A
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # 腾讯财经返回格式：v_sh000001="1~上证指数~3023.45~+12.34~+0.41%"
                content = response.text
                lines = content.split(';')
                print(f"✅ 成功获取 {len(lines)-1} 只股票数据")
                
                # 解析数据
                for line in lines:
                    if line.strip():
                        parts = line.split('~')
                        if len(parts) >= 5:
                            code = parts[1]
                            name = parts[2]
                            price = parts[3]
                            change = parts[4]
                            print(f"📋 {code} - {name}: 价格={price}, 涨跌={change}")
                
                return True
            except Exception as e:
                print(f"❌ 数据解析失败: {e}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始修改版数据接口测试...")
    print("=" * 50)
    
    # 测试结果统计
    results = []
    
    # 东方财富实时数据
    results.append(test_eastmoney_realtime())
    
    # 东方财富历史数据
    results.append(test_eastmoney_historical())
    
    # 腾讯财经实时数据
    results.append(test_tencent_realtime())
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试结果总结:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 所有测试通过！可以开始构建量化系统！")
    else:
        print("⚠️ 部分测试失败，需要继续优化")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)