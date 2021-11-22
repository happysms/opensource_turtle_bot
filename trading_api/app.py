from chalice import Chalice
from chalicelib import util
import time

app = Chalice(app_name='trading_api')


@app.route('/', cors=True)
def index():
    return {"hello": "world"}


@app.route('/trade', methods=['POST'])
def trade():
    request = app.current_request
    data = request.json_body
    try:
        symbol = data['symbol']
        position = data['position']
        target_price = data['target_price']
        trade_condition = data['trade_condition']

    except KeyError:
        raise NotFoundError()

    if trade_condition in ["enter_long", "enter_short"]:
        util.enter_position(symbol, position, target_price)
        return {"message": "success"}

    elif trade_condition in ["exit_long", "exit_short"]:
        util.exit_position(symbol, position, target_price)
        return {"message": "success"}

    return {"message": "fail"}


@app.route('/test')
def test():
    time.sleep(20)
    return {"hello": "world"}
