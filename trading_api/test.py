import requests
from chalicelib import util
import time


def order():
    datas = {
        "symbol": "TRX/USDT",
        "position": "short",
        "target_price": 1,
        "trade_condition": "exit_short"
    }

    headers = {'Content-Type': 'application/json; charset=utf-8'}

    url = "http://localhost:8000/trade"
    res = requests.post(url, json=datas, headers=headers)
    print(res.text)
    trade_list = util.get_trade_list()
    print(trade_list)


start = time.time()

trade_list = util.get_trade_list()
util.write_trade_list()
print(trade_list)
end = time.time()

print("소요시간: ", end-start)
