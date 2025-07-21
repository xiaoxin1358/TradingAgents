print("=== 测试3: 配置文件检查 ===")

import os
import json

# 检查配置文件
config_file = 'tdx_servers_config.json'
print(f"当前工作目录: {os.getcwd()}")
print(f"配置文件路径: {os.path.join(os.getcwd(), config_file)}")

if os.path.exists(config_file):
    print("✅ 配置文件存在")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"📋 配置内容: {config}")
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
else:
    print("⚠️ 配置文件不存在，将创建默认配置")
    
    default_config = {
        "working_servers": [
            {"ip": "119.147.212.81", "port": 7709},
            {"ip": "124.71.85.110", "port": 7709},
            {"ip": "115.238.56.198", "port": 7709},
            {"ip": "115.238.90.165", "port": 7709}
        ]
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 已创建默认配置文件: {config_file}")
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")

# 测试配置加载
try:
    from tradingagents.dataflows.tdx_utils import TongDaXinDataProvider
    provider = TongDaXinDataProvider()
    servers = provider._load_working_servers()
    print(f"📋 加载的服务器列表: {servers}")
except Exception as e:
    print(f"❌ 配置加载测试失败: {e}")