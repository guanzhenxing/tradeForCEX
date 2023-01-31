import json
import logging
import redis
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.INFO)
with open('config.json', 'r') as my_config:
    keys = json.load(my_config)

logger = logging.getLogger("trade")
redis_pool = redis.ConnectionPool(**keys['redis'])
redis_conn = redis.Redis(connection_pool=redis_pool)