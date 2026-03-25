#!/usr/bin/env python3
"""
AKShare 数据接口测试脚本
用于测试AKShare的基本功能和数据质量
"""

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_import():
    """测试基本导入"""
    try:
        print("🔍 测试基本导入...")
        import akshare as ak
        print(f"✅ AKShare版本: {ak.__version__}")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_realtime_data():
    """测试实时数据获取"""
    try:
        print("\n📊 测试实时数据获取...")
        import akshare as ak
        
        # 测试沪深A股实时行情
        print("📈 获取沪深A股实时行情...")
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 获取到 {len(df)} 只股票的实时数据")
        print(f"📋 数据列: {list(df.columns)}")
        
        # 显示前5只股票的信息
        print("\n📋 前5只股票信息:")
        for i, row in df.head().iterrows():
            print(f"{row['代码']} - {row['名称']}: 最新价={row['最新价']}, 涨跌幅={row['涨跌幅']}%")
        
        return True
    except Exception as e:
        print(f"❌ 实时数据获取失败: {e}")
        return False

def test_historical_data():
    """测试历史数据获取"""
    try:
        print("\n📈 测试历史数据获取...")
        import akshare as ak
        
        # 测试万科A的历史数据
        print("📊 获取万科A(000001)历史数据...")
        df = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                               start_date="20240101", end_date="20240321", adjust="")
        print(f"✅ 获取到 {len(df)} 条历史数据")
        print(f"📋 数据列: {list(df.columns)}")
        
        # 显示最近5天的数据
        print("\n📋 最近5天数据:")
        print(df.tail()[['日期', '开盘', '收盘', '最高', '最低', '成交量']])
        
        return True
    except Exception as e:
        print(f"❌ 历史数据获取失败: {e}")
        return False

def test_individual_stock():
    """测试个股信息获取"""
    try:
        print("\n🏢 测试个股信息获取...")
        import akshare as ak
        
        # 测试万科A的个股信息
        print("📊 获取万科A(000001)个股信息...")
        df = ak.stock_individual_info_em(symbol="000001")
        print(f"✅ 获取到个股信息")
        print(f"📋 数据列: {list(df.columns)}")
        
        # 显示重要信息
        print("\n📋 重要信息:")
        for i, row in df.iterrows():
            if row['item'] in ['股票代码', '股票简称', '总股本', '流通股', '总市值', '流通市值', '行业']:
                print(f"{row['item']}: {row['value']}")
        
        return True
    except Exception as e:
        print(f"❌ 个股信息获取失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始AKShare数据接口测试...")
    print("=" * 50)
    
    # 测试结果统计
    results = []
    
    # 基本导入测试
    results.append(test_basic_import())
    
    # 实时数据测试
    results.append(test_realtime_data())
    
    # 历史数据测试
    results.append(test_historical_data())
    
    # 个股信息测试
    results.append(test_individual_stock())
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 测试结果总结:")
    print(f"✅ 成功: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 所有测试通过！AKShare可以正常使用！")
    else:
        print("⚠️ 部分测试失败，需要检查网络连接或数据源")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)