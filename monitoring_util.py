import requests
import json
import boto3
import pandas as pd
import time


def request_order(symbol, position, target_price, trade_condition):
    url = "api gateway"
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    requests.post(url, headers=headers, json={"symbol": symbol,
                                              "position": position,
                                              "target_price": target_price,
                                              "trade_condition": trade_condition})


def check_trading_condition(config, price_info):
    if not config['info']['position']:
        if price_info["now_price"] >= price_info["max_price"]:
            if config['info']['is_start']:
                if (price_info["now_price"] / price_info["max_price"]) < 1.01:  # 첫 시작때는 타겟 오차 2퍼센트 내에서만 포지션 진입
                    return "enter_long"
                else:
                    return None

            return "enter_long"

        elif price_info["now_price"] <= price_info["min_price"]:
            if config['info']['is_start']:
                if (price_info["min_price"] / price_info["now_price"]) < 1.01:  # 첫 시작때는 타겟 오차 2퍼센트 내에서만 포지션 진입
                    return "enter_short"
                else:
                    return None
            return "enter_short"

    elif config['info']['position'] == "long":
        if price_info["now_price"] <= price_info["long_exit_price"]:
            return "exit_long"

    elif config['info']['position'] == "short":
        if price_info["now_price"] >= price_info["long_exit_price"]:
            return "exit_short"

    return None


def get_trade_list():
    with open('config.json', 'r', encoding="UTF-8") as auth_file:
        auth_dict = json.load(auth_file)

    s3_client = boto3.client('s3',
                             aws_access_key_id=auth_dict['AWS_ACCESS_KEY_ID'],
                             aws_secret_access_key=auth_dict['AWS_SECRET_ACCESS_KEY'],
                             region_name=auth_dict['AWS_DEFAULT_REGION'])

    s3_obj = s3_client.get_object(Bucket='minsung-trading', Key='turtle/trade.json')
    s3_data = s3_obj['Body'].read().decode('utf-8')
    trade_list = json.loads(s3_data)

    return trade_list


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
