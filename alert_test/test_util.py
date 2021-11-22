import ccxt
import math
import pymysql
from datetime import datetime
import time
import json
import pandas as pd
import logger
from slacker import Slacker
import requests
import json

logger = logger.make_logger("mylogger")
myToken = "slack token"


def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text})
    logger.info(response)


def get_price_info(config, binance):
    data = binance.fetch_ohlcv(
        symbol=config['symbol'],
        timeframe='1d',
        since=int(time.time() * 1000) - (86400000 * (config['info']['enter'] + 1))
    )

    df = pd.DataFrame(
        data=data,
        columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
    )

    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    max_price = max(df.iloc[:-1]['high'])
    min_price = min(df.iloc[:-1]['low'])
    now_price = df.iloc[-1]['close']
    long_exit_price = min(df.iloc[len(df) - config['info']['exit'] - 1: -1]['low'])
    short_exit_price = max(df.iloc[len(df) - config['info']['exit'] - 1: -1]['high'])
    price_info = {
                  "max_price": max_price,
                  "min_price": min_price,
                  "now_price": now_price,
                  "long_exit_price": long_exit_price,
                  "short_exit_price": short_exit_price
                  }

    return price_info


def check_trading_condition(config, price_info):
    if not config['info']['position']:
        if price_info["now_price"] >= price_info["max_price"]:
            return "enter_long"

        elif price_info["now_price"] <= price_info["min_price"]:
            return "enter_short"

    elif config['info']['position'] == "long":
        if price_info["now_price"] <= price_info["long_exit_price"]:
            return "exit_long"

    elif config['info']['position'] == "short":
        if price_info["now_price"] >= price_info["long_exit_price"]:
            return "exit_short"

    return None


def enter_position(symbol, position):
    with open('config.json', 'r', encoding="UTF-8") as in_file:
        config_list = json.load(in_file)

    for config in config_list:  # get amount & set position
        if config.get("symbol") == symbol:
            config["info"]['position'] = position

            post_message(myToken, "#alert", json.dumps(config))

    logger.info(position + " position " + str(symbol))

    with open('config.json', 'w', encoding="utf-8") as out_file:
        json.dump(config_list, out_file, indent="\t")


def exit_position(symbol, position):
    logger.info(position + " position " + str(symbol))

    with open('config.json', 'r', encoding="UTF-8") as in_file:
        config_list = json.load(in_file)

    for config in config_list:
        if config.get("symbol") == symbol:
            config["info"]['position'] = None
            post_message(myToken, "#alert", json.dumps(config))

    with open('config.json', 'w', encoding="utf-8") as out_file:
        json.dump(config_list, out_file, indent="\t")
