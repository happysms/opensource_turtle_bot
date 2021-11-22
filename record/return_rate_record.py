import ccxt
import pymysql
import pandas as pd
from datetime import datetime, timedelta


class ReturnRateRecord:
    def __init__(self, auth_dict):    
        self.binance = ccxt.binance(config={
                    'apiKey': auth_dict.get("api_key"),
                    'secret': auth_dict.get("secret"),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future'
                    }
                })

        self.conn = pymysql.connect(host="",
                                    user="", password="", db="", charset="utf8")
        self.balance = self.binance.fetch_balance()

    def insert_record_to_database(self):
        sql = "select * from return_rate_record"
        df = pd.read_sql(sql, self.conn)

        rr_df = df.iloc[-1]
        total_balance = self.balance['info']['totalWalletBalance']
        ror = float(total_balance) / rr_df['balance']
        hpr = rr_df['hpr'] * ror
        mdd = ((df['hpr'].cummax() - hpr) / df['hpr'].cummax() * 100).iloc[-1]
        date = (datetime.now() + timedelta(1)).strftime("%Y-%m-%d")

        with self.conn.cursor() as curs:
            sql = """
                    INSERT INTO return_rate_record (datetime, ror, hpr, mdd, balance) 
                               VALUES ('{}', {}, {}, {}, {})""".format(date, ror, hpr, mdd, total_balance)

            curs.execute(sql)
            self.conn.commit()

        self.conn.close()
