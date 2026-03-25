#!/usr/bin/env python3
"""
简化版数据接口测试脚本
直接测试数据源，不依赖AKShare
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime

def test_eastmoney_realtime():
    """测试东方财富实时行情数据"""
    try:
        print("📈 测试东方财富实时行情数据...")
        url = "https://quote.eastmoney.com/center/gridlist.html#hs_a_board"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/center/gridlist.html'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 东方财富数据访问成功")
            # 尝试解析页面内容
            content = response.text
            if 'stock_zh_a_spot_em' in content:
                print("✅ 页面包含AKShare接口引用")
            else:
                print("⚠️ 页面未找到AKShare接口引用")
            
            # 保存页面内容用于分析
            with open('eastmoney_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ 页面内容已保存到 eastmoney_page.html")
            
            return True
        else:
            print(f"❌ 数据访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_sina_realtime():
    """测试新浪财经实时行情数据"""
    try:
        print("\n📈 测试新浪财经实时行情数据...")
        url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2/Market_Center.getHQNodeData"
        
        params = {
            'page': 1,
            'num': 20,
            'sort': 'symbol',
            'asc': 1,
            'node': 'hs_a'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://vip.stock.finance.sina.com.cn/mkt/#hs_a'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ 新浪数据访问成功，获取到 {len(data)} 条数据")
                
                # 显示前5条数据
                for i, item in enumerate(data[:5]):
                    print(f"{i+1}. {item.get('code', 'N/A')} - {item.get('name', 'N/A')}: {item.get('price', 'N/A')}")
                
                return True
            except json.JSONDecodeError:
                print("⚠️ 响应不是有效的JSON格式")
                return False
        else:
            print(f"❌ 数据访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_xueqiu_realtime():
    """测试雪球实时行情数据"""
    try:
        print("\n📈 测试雪球实时行情数据...")
        url = "https://stock.xueqiu.com/v5/stock/quote.json"
        
        params = {
            'symbol': 'SH600000',
            'extend': 'detail'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://xueqiu.com/S/SH600000'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ 雪球数据访问成功")
                
                # 显示基本信息
                quote = data.get('data', {}).get('quote', {})
                if quote:
                    print(f"股票代码: {quote.get('symbol', 'N/A')}")
                    print(f"股票名称: {quote.get('name', 'N/A')}")
                    print(f"当前价格: {quote.get('current', 'N/A')}")
                    print(f"涨跌幅: {quote.get('percent', 'N/A')}%")
                
                return True
            except json.JSONDecodeError:
                print("⚠️ 响应不是有效的JSON格式")
                return False
        else:
            print(f"❌ 数据访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_historical_data():
    """测试历史数据获取"""
    try:
        print("\n📈 测试历史数据获取...")
        # 使用新浪的历史数据接口
        url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2/Market_Center.getHQData"
        
        params = {
            'symbol': 'sh600000',
            'scale': '60day',
            'ma': '5',
            'datalen': '60'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2/Market_Center.getHQData'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ 历史数据访问成功，获取到 {len(data)} 条数据")
                
                # 转换为DataFrame
                if data:
                    df = pd.DataFrame(data)
                    print(f"📋 数据列: {list(df.columns)}")
                    
                    # 显示最近5天的数据
                    print("\n📋 最近5天数据:")
                    print(df[['day', 'open', 'close', 'high', 'low']].tail())
                
                return True
            except json.JSONDecodeError:
                print("⚠️ 响应不是有效的JSON格式")
                return False
        else:
            print(f"❌ 数据访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始简化版数据接口测试...")
    print("=" * 50)
    
    # 测试结果统计
    results = []
    
    # 东方财富测试
    results.append(test_eastmoney_realtime())
    
    # 新浪财经测试
    results.append(test_sina_realtime())
    
    # 雪球测试
    results.append(test_xueqiu_realtime())
    
    # 历史数据测试
    results.append(test_historical_data())
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试结果总结:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 所有数据源访问正常！")
    else:
        print("⚠️ 部分数据源访问失败，需要检查网络连接")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    print(f"\n📊 测试完成，返回码: {0 if success else 1}")
    exit(0 if success else 1)