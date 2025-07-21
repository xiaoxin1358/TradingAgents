print("=== 测试1: pytdx基础功能 ===")

try:
    from pytdx.hq import TdxHq_API
    print("✅ pytdx导入成功")
    
    api = TdxHq_API(heartbeat=True, auto_retry=True)
    print("✅ TdxHq_API实例化成功")
    
    # 测试多个服务器
    servers = [
        ('119.147.212.81', 7709),
        ('124.71.85.110', 7709), 
        ('115.238.56.198', 7709),
        ('115.238.90.165', 7709),
    ]
    
    for ip, port in servers:
        try:
            print(f"\n🔌 尝试连接 {ip}:{port}")
            result = api.connect(ip, port)
            
            if result:
                print(f"✅ 连接成功")
                
                # 测试获取行情
                quotes = api.get_security_quotes([(0, '000001')])
                print(f"📈 行情数据: {quotes}")
                
                # 测试获取股票列表  
                stock_list = api.get_security_list(0, 0)
                print(f"📋 股票列表数量: {len(stock_list) if stock_list else 0}")
                
                if stock_list:
                    print(f"📋 示例股票: {stock_list[:3]}")
                
                api.disconnect()
                print("✅ pytdx工作正常，退出测试")
                break
            else:
                print(f"❌ 连接失败")
                
        except Exception as e:
            print(f"❌ 连接异常: {e}")
    
    api.disconnect()
    
except Exception as e:
    print(f"❌ pytdx基础测试失败: {e}")
    import traceback
    traceback.print_exc()