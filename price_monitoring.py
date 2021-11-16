import ccxt
import pandas as pd
import time
import logger
from trade_util import enter_position, exit_position, get_price_info, check_trading_condition
import json

auth = {"api_key": "입력!",
        "secret": "입력!"}

binance = ccxt.binance(config={
    'apiKey': auth.get("api_key"),
    'secret': auth.get("secret"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

with open('config.json', 'r', encoding="UTF-8") as in_file:
    config_list = json.load(in_file)

logger = logger.make_logger("mylogger")

while True:
    # try:
    for config in config_list:
        price_info = get_price_info(config, binance)
        trading_condition = check_trading_condition(config, price_info)
        print(price_info)
        if trading_condition == "enter_long":
            enter_position(binance, config['symbol'], "long", price_info['max_price'])
            config['info']['position'] = "long"

        elif trading_condition == "enter_short":
            enter_position(binance, config['symbol'], "short", price_info['max_price'])
            config['info']['position'] = "short"

        elif trading_condition == "exit_long":
            exit_position(binance, config['symbol'], "long", price_info['long_exit_price'])
            config['info']['position'] = None

        elif trading_condition == "exit_short":
            exit_position(binance, config['symbol'], "short", price_info['short_exit_price'])
            config['info']['position'] = None

    time.sleep(0.5)
    # except Exception as e:
    #     logger.error(e)
