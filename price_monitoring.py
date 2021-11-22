import ccxt
import pandas as pd
import time
import logger
from monitoring_util import check_trading_condition, request_order, get_trade_list, get_price_info
import json
import requests


binance = ccxt.binance()
logger = logger.make_logger("mylogger")
trade_list = get_trade_list()

while True:
    try:
        for trade in trade_list:
            price_info = get_price_info(trade, binance)
            trade_condition = check_trading_condition(trade, price_info)

            if trade_condition == "enter_long":
                trade['info']['position'] = "long"
                request_order(trade["symbol"], "long", price_info['max_price'], trade_condition)

            elif trade_condition == "enter_short":
                trade['info']['position'] = "short"
                request_order(trade["symbol"], "short", price_info['min_price'], trade_condition)

            elif trade_condition == "exit_long":
                trade['info']['position'] = None
                request_order(trade["symbol"], "long", price_info['long_exit_price'], trade_condition)

            elif trade_condition == "exit_short":
                trade['info']['position'] = None
                request_order(trade["symbol"], "short", price_info['short_exit_price'], trade_condition)

        time.sleep(0.1)

    except Exception as e:
        logger.error(e)
