#!/usr/bin/env python3
"""
腾讯财经历史数据测试
"""

import requests
import pandas as pd
from datetime import datetime
import json

def test_tencent_historical():
    """测试腾讯财经历史数据"""
    try:
        print("📈 测试腾讯财经历史数据...")
        
        # 万科A的历史数据
        symbol = "sz000002"  # sz表示深圳
        url = f"https://qt.gtimg.cn/q={symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # 腾讯财经返回格式：v_sz000002="2~万科A~12.45~+0.05~+0.40%~20240321~12.40~12.50~12.30~12.45~123456~12345678~0.50~0.40~0.30~0.20~0.10~0.05~0.02~0.01~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~0.00~最新数据"
                content = response.text
                
                # 提取数据部分
                if 'v_sz000002=' in content:
                    data_str = content.split('v_sz000002=')[1].split(';')[0]
                    parts = data_str.split('~')
                    
                    if len(parts) > 10:
                        name = parts[1]
                        current_price = parts[2]
                        change = parts[3]
                        change_percent = parts[4]
                        date = parts[5]
                        open_price = parts[6]
                        high_price = parts[7]
                        low_price = parts[8]
                        close_price = parts[9]
                        volume = parts[10]
                        amount = parts[11]
                        
                        print(f"✅ 成功获取{name}({symbol})数据")
                        print(f"📋 基本信息:")
                        print(f"  当前价格: {current_price}")
                        print(f"  涨跌额: {change}")
                        print(f"  涨跌幅: {change_percent}")
                        print(f"  日期: {date}")
                        print(f"  开盘: {open_price}")
                        print(f"  最高: {high_price}")
                        print(f"  最低: {low_price}")
                        print(f"  收盘: {close_price}")
                        print(f"  成交量: {volume}")
                        print(f"  成交额: {amount}")
                        
                        return True
                    else:
                        print("⚠️ 数据格式不正确")
                        return False
                else:
                    print("⚠️ 未找到万科A数据")
                    return False
                    
            except Exception as e:
                print(f"❌ 数据解析失败: {e}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_sina_historical():
    """测试新浪财经历史数据"""
    try:
        print("\n📈 测试新浪财经历史数据...")
        
        # 万科A的历史数据
        symbol = "sz000002"
        url = "https://finance.sina.com.cn/realstock/company/sz000002/nc.shtml"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                content = response.text
                print(f"✅ 成功访问新浪财经页面")
                print(f"📋 页面长度: {len(content)} 字符")
                
                # 查找历史数据表格
                if '历史行情' in content or 'kline' in content:
                    print("✅ 页面包含历史数据")
                    
                    # 保存页面内容用于分析
                    with open('sina_wanke_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("💾 页面内容已保存到 sina_wanke_page.html")
                    
                    return True
                else:
                    print("⚠️ 页面未找到历史数据")
                    return False
                    
            except Exception as e:
                print(f"❌ 页面解析失败: {e}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试历史数据获取...")
    print("=" * 50)
    
    # 测试结果统计
    results = []
    
    # 腾讯财经历史数据
    results.append(test_tencent_historical())
    
    # 新浪财经历史数据
    results.append(test_sina_historical())
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试结果总结:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if any(results):
        print("🎉 至少有一种历史数据获取方式成功！")
    else:
        print("⚠️ 所有历史数据获取失败")

if __name__ == "__main__":
    main()