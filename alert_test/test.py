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


myToken = "slack token"

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text})


post_message(myToken, "#alert", json.dumps({"Test1": "Test2"}))
