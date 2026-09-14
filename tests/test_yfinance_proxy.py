import os

import yfinance as yf

proxy = 'http://127.0.0.1:9910' # 代理设置，此处修改
os.environ['HTTP_PROXY'] = proxy
os.environ['HTTPS_PROXY'] = proxy


start_date = '2005-04-01'
end_date = '2025-04-30'

tickers = ['APP', 'TSLA']
data = yf.download(tickers, start_date, end_date, progress = False)['Close']
data = data.pct_change().dropna()
data = data[tickers]
print(data[tickers])

'''$env:HTTP_PROXY='http://127.0.0.1:9910'; $env:HTTPS_PROXY='http://127.0.0.1:9910'''
