from binance.spot import Spot
from config import keys
client = Spot()

# Get server timestamp
print(client.time())
# Get klines of BTCUSDT at 1m interval
print(client.klines("BTCUSDT", "1m"))
# Get last 10 klines of BNBUSDT at 1h interval
print(client.klines("BNBUSDT", "1h", limit=10))

# API key/secret are required for user data endpoints
client = Spot(api_key=keys["binance_api_key"], api_secret=keys["binance_secret_key"])

# Get account and balance information
print(client.account())
