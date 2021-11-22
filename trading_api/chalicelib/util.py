import ccxt
import math
import pymysql
from datetime import datetime
import time
import json
import logging
import boto3
import os


def make_logger(name=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.propagate = False

    return logger


logger = make_logger("mylogger")


def get_database_connection():
    with open(os.path.dirname(os.path.realpath(__file__))+'/config.json', 'r', encoding="UTF-8") as auth_file:
        auth_dict = json.load(auth_file)

    conn = pymysql.connect(host=auth_dict["host"],
                           user=auth_dict["user"], password=auth_dict["password"], db=auth_dict["db"], charset="utf8")

    return conn


def get_binance_object():
    with open(os.path.dirname(os.path.realpath(__file__))+'/config.json', 'r', encoding="UTF-8") as auth_file:
        auth_dict = json.load(auth_file)
        binance = ccxt.binance(config={
            'apiKey': auth_dict.get("api_key"),
            'secret': auth_dict.get("secret"),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })

    return binance


def get_trade_list():
    with open(os.path.dirname(os.path.realpath(__file__))+'/config.json', 'r', encoding="UTF-8") as auth_file:
        auth_dict = json.load(auth_file)

    s3_client = boto3.client('s3',
                             aws_access_key_id=auth_dict['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=auth_dict['AWS_SECRET_ACCESS_KEY'],
                             region_name=auth_dict['AWS_DEFAULT_REGION'])

    s3_obj = s3_client.get_object(Bucket='minsung-trading', Key='turtle/trade.json')
    s3_data = s3_obj['Body'].read().decode('utf-8')
    trade_list = json.loads(s3_data)

    return trade_list


def write_trade_list(symbol, position, dollar=None):
    with open(os.path.dirname(os.path.realpath(__file__))+'/config.json', 'r', encoding="UTF-8") as auth_file:
        auth_dict = json.load(auth_file)

    s3_client = boto3.client('s3',
                             aws_access_key_id=auth_dict['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=auth_dict['AWS_SECRET_ACCESS_KEY'],
                             region_name=auth_dict['AWS_DEFAULT_REGION'])

    s3_obj = s3_client.get_object(Bucket='minsung-trading', Key='turtle/trade.json')
    s3_data = s3_obj['Body'].read().decode('utf-8')
    before_trade_list = json.loads(s3_data)

    for trade in before_trade_list:  # get amount & set position
        if trade.get("symbol") == symbol:
            trade["info"]['position'] = position

            if trade['info']['is_start']:
                trade['info']['is_start'] = False

            if dollar:
                trade['info']['dollar'] = dollar

            break

    s3_client.put_object(
        Body=json.dumps(before_trade_list),
        Bucket='minsung-trading',
        Key='turtle/trade.json'
    )


def enter_position(symbol, position, target_price):
    binance = get_binance_object()
    trade_list = get_trade_list()
    usdt = 0

    for trade in trade_list:  # get amount & set position
        if trade.get("symbol") == symbol:
            trade["info"]['position'] = position
            usdt = trade["info"]['dollar']

            if trade['info']['is_start']:
                trade['info']['is_start'] = False

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

    write_trade_list(symbol, position)


def exit_position(symbol, position, target_price):
    binance = get_binance_object()
    amount = cal_exit_possible_amount(binance, symbol)
    dollar = 0

    if position == "long":
        order = binance.create_market_sell_order(symbol=symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)

        record = binance.fetch_order(order_id, symbol)['info']
        dollar = float(record['cumQuote'])
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    else:
        order = binance.create_market_buy_order(symbol=symbol, amount=amount)
        order_id = order['info']['orderId']
        time.sleep(5)

        record = binance.fetch_order(order_id, symbol)['info']
        dollar = float(record['cumQuote'])
        add_record_log(order_id, binance, symbol, target_price)
        logger.info(position + " position " + str(symbol) + " " + str(amount) + "개")

    write_trade_list(symbol, None, dollar)


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

    return 0


def add_record_log(order_id, binance, symbol, target):
    conn = get_database_connection()
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

