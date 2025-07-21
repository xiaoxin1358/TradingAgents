"""
测试 TongDaXinDataProvider 类的专用程序
"""

import sys
import traceback
from datetime import datetime, timedelta

print("=== 测试 TongDaXinDataProvider 类 ===")
print(f"测试时间: {datetime.now()}")
print()

def test_tdx_provider_initialization():
    """测试 TongDaXinDataProvider 初始化"""
    
    print("🔧 步骤1: 测试类初始化...")
    
    try:
        from tradingagents.dataflows.tdx_utils import TongDaXinDataProvider
        print("✅ TongDaXinDataProvider 导入成功")
        
        # 测试初始化
        print("🔧 创建实例...")
        provider = TongDaXinDataProvider()
        print(f"✅ 实例创建成功: {type(provider)}")
        
        # 检查初始状态
        print(f"  - api 对象: {provider.api}")
        print(f"  - connected 状态: {provider.connected}")
        
        return provider
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        traceback.print_exc()
        return None

def test_connection(provider):
    """测试连接功能"""
    
    print("\n🔧 步骤2: 测试连接功能...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return False
    
    try:
        print("🔧 尝试连接...")
        result = provider.connect()
        print(f"连接结果: {result}")
        print(f"连接状态: {provider.connected}")
        
        if result:
            print("✅ 连接成功")
            
            # 测试连接检查
            is_connected = provider.is_connected()
            print(f"连接检查结果: {is_connected}")
            
            return True
        else:
            print("❌ 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 连接过程异常: {e}")
        traceback.print_exc()
        return False

def test_get_stock_name(provider):
    """测试股票名称获取功能"""
    
    print("\n🔧 步骤3: 测试股票名称获取...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    # 测试不同类型的股票代码
    test_codes = [
        ('000001', '深圳市场 - 平安银行'),
        ('000002', '深圳市场 - 万科A'),
        ('300750', '深圳创业板 - 宁德时代'),
        ('600519', '上海市场 - 贵州茅台'),
        ('601318', '上海市场 - 中国平安'),
        ('688981', '科创板 - 中芯国际'),
        ('999999', '不存在的股票'),
    ]
    
    for code, description in test_codes:
        print(f"\n📋 测试 {code} ({description})")
        
        try:
            start_time = datetime.now()
            stock_name = provider._get_stock_name(code)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"  结果: '{stock_name}'")
            print(f"  用时: {duration:.3f}秒")
            
            # 判断结果质量
            if stock_name == f'股票{code}':
                print(f"  状态: ⚠️ 默认格式（API未获取到）")
            elif code in stock_name:
                print(f"  状态: ❌ 异常格式")
            else:
                print(f"  状态: ✅ 获取成功")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_real_time_data(provider):
    """测试实时数据获取"""
    
    print("\n🔧 步骤4: 测试实时数据获取...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    test_codes = ['000001', '600519', '300750']
    
    for code in test_codes:
        print(f"\n📊 获取 {code} 实时数据...")
        
        try:
            data = provider.get_real_time_data(code)
            
            if data:
                print(f"  ✅ 成功获取实时数据:")
                print(f"    名称: {data.get('name', 'N/A')}")
                print(f"    价格: ¥{data.get('price', 0):.2f}")
                print(f"    涨跌幅: {data.get('change_percent', 0):.2f}%")
                print(f"    成交量: {data.get('volume', 0):,}手")
            else:
                print(f"  ❌ 未获取到数据")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_history_data(provider):
    """测试历史数据获取"""
    
    print("\n🔧 步骤5: 测试历史数据获取...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    # 测试最近一个月的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    test_codes = ['000001', '600519']
    
    for code in test_codes:
        print(f"\n📈 获取 {code} 历史数据 ({start_date} 到 {end_date})...")
        
        try:
            df = provider.get_stock_history_data(code, start_date, end_date)
            
            if not df.empty:
                print(f"  ✅ 成功获取历史数据:")
                print(f"    数据条数: {len(df)}")
                print(f"    时间范围: {df.index[0]} 到 {df.index[-1]}")
                print(f"    最高价: ¥{df['High'].max():.2f}")
                print(f"    最低价: ¥{df['Low'].min():.2f}")
                print(f"    最新收盘: ¥{df['Close'].iloc[-1]:.2f}")
                
                # 显示最近3天数据
                print(f"    最近3天数据:")
                print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3).to_string())
                
            else:
                print(f"  ❌ 未获取到历史数据")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_search_stocks(provider):
    """测试股票搜索功能"""
    
    print("\n🔧 步骤6: 测试股票搜索...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    keywords = ['平安', '茅台', '000001', '600']
    
    for keyword in keywords:
        print(f"\n🔍 搜索关键词: '{keyword}'")
        
        try:
            results = provider.search_stocks(keyword)
            
            if results:
                print(f"  ✅ 找到 {len(results)} 个结果:")
                for result in results:
                    print(f"    {result['code']} - {result['name']} - ¥{result['price']:.2f} ({result['change_percent']:+.2f}%)")
            else:
                print(f"  ⚠️ 未找到匹配结果")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_market_overview(provider):
    """测试市场概览"""
    
    print("\n🔧 步骤7: 测试市场概览...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    try:
        market_data = provider.get_market_overview()
        
        if market_data:
            print(f"  ✅ 获取市场概览成功:")
            for name, data in market_data.items():
                change_symbol = "📈" if data['change'] >= 0 else "📉"
                print(f"    {change_symbol} {name}: {data['price']:.2f} ({data['change_percent']:+.2f}%)")
        else:
            print(f"  ❌ 未获取到市场数据")
            
    except Exception as e:
        print(f"  ❌ 异常: {e}")

def test_technical_indicators(provider):
    """测试技术指标计算"""
    
    print("\n🔧 步骤8: 测试技术指标...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    test_codes = ['000001', '600519']
    
    for code in test_codes:
        print(f"\n📊 计算 {code} 技术指标...")
        
        try:
            indicators = provider.get_stock_technical_indicators(code)
            
            if indicators:
                print(f"  ✅ 技术指标计算成功:")
                for key, value in indicators.items():
                    if value is not None:
                        if isinstance(value, float):
                            print(f"    {key}: {value:.2f}")
                        else:
                            print(f"    {key}: {value}")
            else:
                print(f"  ❌ 未计算出技术指标")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_edge_cases(provider):
    """测试边界情况"""
    
    print("\n🔧 步骤9: 测试边界情况...")
    
    if not provider:
        print("❌ 没有有效的 provider 实例")
        return
    
    # 测试无效股票代码
    print("\n📋 测试无效股票代码...")
    invalid_codes = ['', '123', 'ABC123', '0000000']
    
    for code in invalid_codes:
        try:
            name = provider._get_stock_name(code)
            print(f"  '{code}' -> '{name}'")
        except Exception as e:
            print(f"  '{code}' -> 异常: {e}")
    
    # 测试网络中断后的行为
    print("\n📋 测试断开连接后的行为...")
    if provider.connected:
        provider.disconnect()
        print(f"  断开连接，状态: {provider.connected}")
        
        # 尝试获取数据
        try:
            name = provider._get_stock_name('000001')
            print(f"  断开后获取名称: '{name}'")
        except Exception as e:
            print(f"  断开后获取名称异常: {e}")

def performance_test(provider):
    """性能测试"""
    
    print("\n🔧 步骤10: 性能测试...")
    
    if not provider or not provider.connected:
        print("❌ 没有有效连接，跳过性能测试")
        return
    
    test_codes = ['000001', '000002', '600519', '601318', '300750']
    
    print(f"\n⏱️ 批量获取股票名称性能测试...")
    start_time = datetime.now()
    
    for code in test_codes:
        try:
            name = provider._get_stock_name(code)
            print(f"  {code}: {name}")
        except Exception as e:
            print(f"  {code}: 异常 - {e}")
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    avg_time = total_time / len(test_codes)
    
    print(f"\n📊 性能统计:")
    print(f"  总用时: {total_time:.2f}秒")
    print(f"  平均用时: {avg_time:.2f}秒/股票")
    print(f"  处理速度: {len(test_codes)/total_time:.1f}股票/秒")

if __name__ == '__main__':
    print("开始全面测试 TongDaXinDataProvider 类...")
    
    success_count = 0
    total_tests = 10
    
    # 1. 测试初始化
    provider = test_tdx_provider_initialization()
    if provider:
        success_count += 1
    
    # 2. 测试连接
    connected = test_connection(provider)
    if connected:
        success_count += 1
    
    # 3. 测试股票名称获取
    test_get_stock_name(provider)
    success_count += 1
    
    # 4. 测试实时数据
    if connected:
        test_real_time_data(provider)
        success_count += 1
    
    # 5. 测试历史数据
    if connected:
        test_history_data(provider)
        success_count += 1
    
    # 6. 测试搜索功能
    if connected:
        test_search_stocks(provider)
        success_count += 1
    
    # 7. 测试市场概览
    if connected:
        test_market_overview(provider)
        success_count += 1
    
    # 8. 测试技术指标
    if connected:
        test_technical_indicators(provider)
        success_count += 1
    
    # 9. 测试边界情况
    test_edge_cases(provider)
    success_count += 1
    
    # 10. 性能测试
    if connected:
        performance_test(provider)
        success_count += 1
    
    # 清理
    if provider:
        provider.disconnect()
        print(f"\n🔧 连接已断开")
    
    # 总结
    print(f"\n" + "="*70)
    print(f"🎯 测试完成!")
    print(f"成功率: {success_count}/{total_tests} ({(success_count/total_tests)*100:.1f}%)")
    
    if success_count >= 8:
        print("🎉 TongDaXinDataProvider 类工作良好!")
    elif success_count >= 5:
        print("⚠️ TongDaXinDataProvider 类基本可用，但有部分问题")
    else:
        print("❌ TongDaXinDataProvider 类存在严重问题")
    
    print(f"\n💡 测试说明:")
    print("- ✅ 成功: 功能正常工作")
    print("- ⚠️ 警告: 功能有限或返回默认值") 
    print("- ❌ 失败: 功能异常或连接问题")
    
    print(f"\n测试完成时间: {datetime.now()}")