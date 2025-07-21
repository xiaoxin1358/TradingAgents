'''
from pytdx.hq import TdxHq_API
#api = TdxHq_API()
api = TdxHq_API(heartbeat=True,auto_retry=True)#心跳包，这样就不会掉线；加入断线重新连接
with api.connect('124.71.85.110', 7709):  # 通达信行情站地址、端口
    d = api.get_security_quotes([(0, '000988'), (1, '605011')])  # 0 深圳，1 上海
    print(d)
'''
import pytdx
from tradingagents.api.stock_api import get_stock_data_service

service = get_stock_data_service()  # 获取服务实例

# 使用正确的方法名
a = service.get_stock_basic_info('000001')  # ← 修改这里


print("基本信息:", a)

