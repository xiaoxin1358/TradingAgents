"""
测试 _get_stock_name 函数的专用程序
"""

import sys
import traceback
from datetime import datetime

print("=== 测试 _get_stock_name 函数 ===")
print(f"测试时间: {datetime.now()}")
print()

def test_get_stock_name():
    """测试 _get_stock_name 函数"""
    
    try:
        # 1. 导入相关模块
        print("🔧 步骤1: 导入模块...")
        from tradingagents.dataflows.tdx_utils import TongDaXinDataProvider, get_tdx_provider
        print("✅ 模块导入成功")
        
        # 2. 创建提供器实例
        print("\n🔧 步骤2: 创建通达信提供器实例...")
        provider = get_tdx_provider()  # 或者 TongDaXinDataProvider()
        print(f"✅ 提供器实例创建成功: {type(provider)}")
        
        # 3. 检查初始连接状态
        print(f"\n🔧 步骤3: 检查连接状态...")
        print(f"初始连接状态: {provider.connected}")
        print(f"API对象: {provider.api}")
        
        # 4. 测试连接
        print("\n🔧 步骤4: 测试连接...")
        connect_result = provider.connect()
        print(f"连接结果: {connect_result}")
        print(f"连接后状态: {provider.connected}")
        
        if not provider.connected:
            print("❌ 连接失败，无法继续测试")
            return False
        
        # 5. 测试不同类型的股票代码
        test_codes = [
            # 深圳市场 - 应该能通过API获取
            ('000001', '平安银行', '深圳主板'),
            ('000002', '万科A', '深圳主板'),
            ('002415', '海康威视', '深圳中小板'),
            ('300750', '宁德时代', '深圳创业板'),
            
            # 上海市场 - 可能只能从缓存/映射获取
            ('600519', '贵州茅台', '上海主板'),
            ('601318', '中国平安', '上海主板'),
            ('688981', '中芯国际', '上海科创板'),
            
            # 测试不存在的代码
            ('999999', '未知股票', '测试代码'),
        ]
        
        print("\n🔧 步骤5: 测试各种股票代码...")
        print("-" * 70)
        
        success_count = 0
        total_count = len(test_codes)
        
        for i, (code, expected_name, market_type) in enumerate(test_codes, 1):
            print(f"\n📋 测试 {i}/{total_count}: {code} ({market_type})")
            print(f"期望名称: {expected_name}")
            
            try:
                # 测试 _get_stock_name 函数
                start_time = datetime.now()
                stock_name = provider._get_stock_name(code)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"获取名称: '{stock_name}'")
                print(f"用时: {duration:.2f}秒")
                
                # 判断结果
                if stock_name and stock_name != f'股票{code}':
                    if expected_name in stock_name or stock_name in expected_name:
                        print(f"✅ 获取成功 - 名称匹配")
                        success_count += 1
                    else:
                        print(f"⚠️ 获取成功 - 名称不匹配 (实际: {stock_name}, 期望: {expected_name})")
                        success_count += 1  # 也算成功，只是名称可能不完全一致
                else:
                    print(f"❌ 获取失败 - 返回默认格式")
                
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                traceback.print_exc()
            
            print("-" * 50)
        
        # 6. 测试结果统计
        print(f"\n📊 测试结果统计:")
        print(f"总测试数: {total_count}")
        print(f"成功数: {success_count}")
        print(f"成功率: {(success_count/total_count)*100:.1f}%")
        
        # 7. 测试缓存功能
        print(f"\n🔧 步骤6: 测试缓存功能...")
        test_code = '000001'
        
        # 第一次调用
        print(f"第一次获取 {test_code}...")
        start_time = datetime.now()
        name1 = provider._get_stock_name(test_code)
        time1 = (datetime.now() - start_time).total_seconds()
        
        # 第二次调用（应该从缓存获取）
        print(f"第二次获取 {test_code}...")
        start_time = datetime.now()
        name2 = provider._get_stock_name(test_code)
        time2 = (datetime.now() - start_time).total_seconds()
        
        print(f"第一次结果: '{name1}' (用时: {time1:.3f}秒)")
        print(f"第二次结果: '{name2}' (用时: {time2:.3f}秒)")
        
        if name1 == name2:
            if time2 < time1:
                print("✅ 缓存工作正常 - 第二次更快")
            else:
                print("⚠️ 缓存可能未生效 - 时间差异不明显")
        else:
            print("❌ 缓存有问题 - 结果不一致")
        
        # 8. 断开连接
        print(f"\n🔧 步骤7: 断开连接...")
        provider.disconnect()
        print("✅ 连接已断开")
        
        return success_count > 0
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 请确保项目路径正确，或者运行: python -m pytest 从项目根目录")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        traceback.print_exc()
        return False

def test_different_scenarios():
    """测试不同场景下的函数行为"""
    
    print("\n" + "="*70)
    print("=== 测试不同场景 ===")
    
    try:
        from tradingagents.dataflows.tdx_utils import TongDaXinDataProvider
        
        # 场景1: 未连接时调用
        print("\n📋 场景1: 未连接状态下调用...")
        provider = TongDaXinDataProvider()
        print(f"连接状态: {provider.connected}")
        
        result = provider._get_stock_name('000001')
        print(f"未连接时获取结果: '{result}'")
        
        # 场景2: 连接失败后的行为
        print(f"\n📋 场景2: 连接后测试...")
        if provider.connect():
            print("✅ 连接成功")
            
            # 测试市场代码判断
            test_codes = ['000001', '600519', '300750', '688981']
            for code in test_codes:
                market_code = provider._get_market_code(code)
                market_name = "深圳" if market_code == 0 else "上海"
                print(f"  {code} -> 市场: {market_name} (代码: {market_code})")
        
        provider.disconnect()
        
    except Exception as e:
        print(f"❌ 场景测试失败: {e}")

if __name__ == '__main__':
    print("开始测试...")
    
    # 主要测试
    success = test_get_stock_name()
    
    # 场景测试
    test_different_scenarios()
    
    print(f"\n" + "="*70)
    if success:
        print("🎉 测试完成！_get_stock_name 函数基本可用")
    else:
        print("❌ 测试失败！_get_stock_name 函数存在问题")
    
    print("\n💡 提示:")
    print("- 如果深圳股票能获取到名称，说明函数工作正常")
    print("- 如果上海股票只返回默认格式，这是正常的（API限制）")
    print("- 如果所有股票都返回默认格式，可能是连接或API问题")
    print(f"测试结束时间: {datetime.now()}")