import json
import logging
import redis
from binance.spot import Spot
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.INFO)
with open('config.json', 'r') as my_config:
    keys = json.load(my_config)

logger = logging.getLogger("trade")
redis_pool = redis.ConnectionPool(**keys['redis'])
redis_conn = redis.Redis(connection_pool=redis_pool)
client = Spot(base_url=keys["base_url"],api_key=keys["binance_api_key"], api_secret=keys["binance_secret_key"])