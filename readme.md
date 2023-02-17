# 1.介绍
在币安可以使用的马丁格尔策略，支持btc对稳定币，因为币安现在btc对稳定币是免手续费的，其他交易对后续再考虑吧。
#
# 2.配置详解
``` json
{
    # 配置redis
    "redis": {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0,
        "password": ""
    },
    # 配置mysql
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "username": "ops",
        "passwd": "wblocaldev",
        "database": "trade"
    },
    # 将币安的api-key写进去
    "binance_api_key": "",
    "binance_secret_key": "",
    # 要运行的交易对
    "symbol": "BTCBUSD",
    # 限制总买单的上限
    "limit_usd": 2000,
    # 第一笔市价买单
    "first_order_usd": 100,
    # 第一笔加仓买单
    "first_raise_position_usd": 120,
    # 每次加仓的比率
    "multiplier_of_position_increase_amount": 1.1,
    # 下跌多少加仓
    "down_how_much_to_add_to_the_position": 0.01,
    # 止盈单收益（已成交买单的比率）
    "profit_target": 0.01,
    # api接口 
    # 正式环境：https://api.binance.com
    # 测试环境：
    "base_url": "https://testnet.binance.vision"
  }
```
#
# 3.建表语句
``` sql
CREATE DATABASE `trade` ;
CREATE TABLE `trade_history` (
  `round` int DEFAULT NULL COMMENT '轮次',
  `id` tinyint DEFAULT NULL COMMENT '每个轮次的挂单编号',
  `order_id` int DEFAULT NULL COMMENT '挂单ID',
  `symbol` varchar(32) DEFAULT NULL COMMENT '交易对',
  `side` tinyint DEFAULT NULL COMMENT '0表示买，1表示卖',
  `order_price` float DEFAULT NULL COMMENT '挂单价格',
  `order_amount` float DEFAULT NULL COMMENT '挂单数量',
  `done` tinyint(1) DEFAULT NULL COMMENT '是否完全成交'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```
# 
# 4.已知问题
## 1.现在加仓单限制只能10单，后续改掉。
## 2.服务如果挂掉的话，止盈单就不会更新了，所以可能不会全部卖出。

