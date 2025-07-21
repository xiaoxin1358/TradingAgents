print("=== 测试2: TongDaXinDataProvider ===")

try:
    from tradingagents.dataflows.tdx_utils import TongDaXinDataProvider, get_tdx_provider
    print("✅ tdx_utils导入成功")
    
    # 方法1：直接实例化
    provider1 = TongDaXinDataProvider()
    print(f"📦 直接实例化: {provider1}")
    
    # 方法2：通过工厂函数
    try:
        provider2 = get_tdx_provider()
        print(f"📦 工厂函数: {provider2}")
    except Exception as e:
        print(f"❌ 工厂函数失败: {e}")
        provider2 = None
    
    # 选择一个可用的provider进行测试
    provider = provider1 if provider1 else provider2
    
    if provider:
        print(f"\n🔧 测试provider连接...")
        print(f"初始连接状态: {provider.connected}")
        
        # 测试连接
        connect_result = provider.connect()
        print(f"连接结果: {connect_result}")
        print(f"连接后状态: {provider.connected}")
        
        # 如果连接成功，测试获取股票名称
        if provider.connected:
            test_name = provider._get_stock_name('000001')
            print(f"获取000001名称: '{test_name}'")
            
            # 测试搜索功能
            try:
                search_result = provider.search_stocks('平安')
                print(f"搜索'平安': {len(search_result) if search_result else 0}条结果")
                if search_result:
                    print(f"搜索示例: {search_result[:2]}")
            except Exception as e:
                print(f"搜索功能异常: {e}")
        else:
            print("❌ provider连接失败")
    
except Exception as e:
    print(f"❌ TongDaXinDataProvider测试失败: {e}")
    import traceback
    traceback.print_exc()