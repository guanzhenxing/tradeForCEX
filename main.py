from binance.spot import Spot
from config import keys
client = Spot()

# Get server timestamp
print(client.time())

# API key/secret are required for user data endpoints
client = Spot(api_key=keys["binance_api_key"], api_secret=keys["binance_secret_key"])

# Get account and balance information
print(client.account())

print(client.get_orders())
