print("=== 测试4: StockDataService初始化 ===")

try:
    from tradingagents.api.stock_api import get_stock_data_service
    print("✅ stock_api导入成功")
    
    # 获取服务实例
    service = get_stock_data_service()
    print(f"📦 服务实例: {service}")
    print(f"服务类型: {type(service)}")
    
    # 检查重要属性
    print(f"\n🔧 检查服务属性:")
    print(f"  - db_manager: {getattr(service, 'db_manager', '未定义')}")
    print(f"  - tdx_provider: {getattr(service, 'tdx_provider', '未定义')}")
    
    # 检查是否有_get_from_tdx_api方法
    has_enhanced = hasattr(service, '_get_from_tdx_api')
    print(f"  - 增强获取器可用: {has_enhanced}")
    
    if service.tdx_provider:
        print(f"  - tdx_provider类型: {type(service.tdx_provider)}")
        print(f"  - tdx_provider连接状态: {getattr(service.tdx_provider, 'connected', '未定义')}")
        
        # 手动测试通达信提供器
        if hasattr(service.tdx_provider, 'connect'):
            try:
                connect_result = service.tdx_provider.connect()
                print(f"  - 手动连接结果: {connect_result}")
            except Exception as e:
                print(f"  - 手动连接失败: {e}")
    
    # 测试_get_from_tdx_api方法（如果存在）
    if has_enhanced:
        print(f"\n🔧 测试增强获取器:")
        try:
            result = service._get_from_tdx_api('000001')
            print(f"增强获取器结果: {result}")
        except Exception as e:
            print(f"❌ 增强获取器失败: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ StockDataService初始化测试失败: {e}")
    import traceback
    traceback.print_exc()