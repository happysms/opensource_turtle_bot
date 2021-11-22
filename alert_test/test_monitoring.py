import ccxt
import pandas as pd
import time
import logger
from test_util import enter_position, exit_position, get_price_info, check_trading_condition
import json


binance = ccxt.binance()

with open('config.json', 'r', encoding="UTF-8") as in_file:
    config_list = json.load(in_file)

logger = logger.make_logger("mylogger")

while True:
    try:
        for config in config_list:
            price_info = get_price_info(config, binance)
            trading_condition = check_trading_condition(config, price_info)
            if trading_condition == "enter_long":
                enter_position(config['symbol'], "long")
                config['info']['position'] = "long"
    
            elif trading_condition == "enter_short":
                enter_position(config['symbol'], "short")
                config['info']['position'] = "short"
    
            elif trading_condition == "exit_long":
                exit_position(config['symbol'], "long")
                config['info']['position'] = None
    
            elif trading_condition == "exit_short":
                exit_position(config['symbol'], "short")
                config['info']['position'] = None

            time.sleep(0.2)
            print(trading_condition)

    except Exception as e:
        logger.error(e)
