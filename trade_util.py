import ccxt
import math
import pymysql
from datetime import datetime
import time
import json
import pandas as pd
import logger

logger = logger.make_logger("mylogger")


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
    long_exit_price = min(df.iloc[len(df) - config['info']['exit'] - 1:-1]['low'])
    short_exit_price = max(df.iloc[len(df) - config['info']['exit'] - 1:-1]['high'])
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


def cal_enter_possible_amount(binance, symbol, usdt):
    ticker = binance.fetch_ticker(symbol=symbol)
    cur_price = ticker['last']
    amount = math.floor((usdt * 1000000) / cur_price) / 1000000
    return amount


def cal_exit_possible_amount(binance, symbol):
    orig_symbol = symbol.replace("/", "")
    balance = binance.fetch_balance()

    for sym in balance['info']['positions']:
        if sym['symbol'] == orig_symbol:
            amount = abs(float(sym['positionAmt']))
            return amount


def enter_position(binance, symbol, position, target_price):
    with open('config.json', 'r', encoding="UTF-8") as in_file:
        config_list = json.load(in_file)

    for config in config_list:  # get amount & set position
        if config.get("symbol") == symbol:
            config["info"]['position'] = position
            usdt = config["info"]['dollar']
    
    amount = cal_enter_possible_amount(binance, symbol, usdt)

    if position == "long":
        order = binance.create_market_buy_order(symbol=symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    else:
        order = binance.create_market_sell_order(symbol=symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    with open('config.json', 'w', encoding="utf-8") as out_file:
        json.dump(config_list, out_file, indent="\t")
    

def exit_position(binance, symbol, position, target_price):
    amount = cal_exit_possible_amount(binance, symbol)
    dollar = 0

    if position == "long":
        order = binance.create_market_sell_order(symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)

        record = binance.fetch_order(order_id, symbol)['info']
        dollar = float(record['cumQuote'])
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    else:
        order = binance.create_marget_sell_order(symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)

        record = binance.fetch_order(order_id, symbol)['info']
        dollar = float(record['cumQuote'])
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    with open('config.json', 'r', encoding="UTF-8") as in_file:
        config_list = json.load(in_file)

    for config in config_list:  # set position, dollar
        if config.get("symbol") == symbol:
            config["info"]['position'] = None
            config["info"]['dollar'] = dollar

    with open('config.json', 'w', encoding="utf-8") as out_file:
        json.dump(config_list, out_file, indent="\t")


def add_record_log(order_id, binance, symbol, target):
    conn = pymysql.connect(host="입력!",
                           user="입력!", password="입력!", db="입력!", charset="입력!")

    record = binance.fetch_order(order_id, symbol)['info']
    avg_price = float(record['avgPrice'])
    executed_qty = float(record['executedQty'])
    side = record['side']
    status = record['status']
    _type = record['type']
    symbol = record['symbol']
    time = datetime.fromtimestamp(int(record['time']) / 1000)
    fee = float(record['cumQuote']) * 0.0004
    cum_quote = float(record['cumQuote'])
    name = symbol.replace("USDT", "").lower()

    if side.lower() == "buy":
        trade_diff_rate = round(((((avg_price / target)) - 1) * 100), 4)
    else:
        trade_diff_rate = round(((((target / avg_price)) - 1) * 100), 4)

    with conn.cursor() as curs:
        sql = """
                INSERT INTO {} (avg_price, executed_qty, fee, cum_quote, side, 
                            status, type, symbol, datetime, trade_diff_rate, target_price) 
                            VALUES ({}, {}, {}, {}, '{}', '{}', '{}', '{}', '{}', {}, {})
                            """.format(name, avg_price, executed_qty, fee, cum_quote, side,
                                       status, _type, symbol, time, trade_diff_rate, target)

        curs.execute(sql)
        conn.commit()
