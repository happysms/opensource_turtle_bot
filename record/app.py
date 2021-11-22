from record.return_rate_record import ReturnRateRecord

def lambda_handler(event, context):
    auth_dict = {"api_key": "binance api_key",
                 "secret": "binance_secret_key"}

    obj = ReturnRateRecord(auth_dict)
    obj.insert_record_to_database()
