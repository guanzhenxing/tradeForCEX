from .mysqlConnect import OPMysql
from config import client
from config import redis_conn
from config import logger
import time
from config import keys


def getRoundStatus(round):
    '''
    根据传入的round,查询当前round的订单状态是否已完成
    返回1, 表示当前round还在运行。
    返回0, 表示当前round已结束。
    '''
    mysql_client = OPMysql()
    sql = "SELECT order_id from trade_history where round={0} and done=0;"
    res = mysql_client.op_select(sql.format(round))
    if len(res) > 0:
        return 1
    else:
        return 0


def getOrderStatus(order_id):
    '''
    查询订单状态
    '''
    params = {
        "symbol": keys["symbol"],
        "orderId": order_id
    }
    res = client.get_order(**params)
    return res


def getRound():
    '''
    获取本轮策略交易编号
    '''
    if redis_conn.exists("round"):
        round = redis_conn.get("round")
    else:
        round = 0
    return round

def setRound(round):
    '''
    设置策略交易编号
    '''
    try:
        redis_conn.set("round", round)
        logger.info("设置round为{0}".format(round))
    except:
        logger.info("设置round为{0}失败".format(round))


def setLatestOpenBuyOrderId(round):
    '''
    将最新未成交买单塞进redis
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round={} and done=0 and id < 11 order by id asc limit 1;"
    res_list =  mysql_client.op_select(sql.format(round))
    # 如果结果为空
    if len(res_list) == 0:
        redis_conn.set("latest:open:buy:order_id", 0)
    else:
        order_id = res_list[0]["order_id"]
        redis_conn.set("latest:open:buy:order_id", order_id)
        logger.info("设置最新未成交订单id: {0}".format(order_id))

def getLatestOpenBuyOrderId():
    order_id = redis_conn.get("latest:open:buy:order_id")
    return order_id


def getSellOrderId(round):
    '''
    获取卖单的订单id
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round = {0} and id = 11;"
    res = mysql_client.op_select(sql.format(round))
    return res[0].get("order_id",None)

def setOrderInfo(**kwargs):
    '''
    将订单信息入库
    '''
    mysql_client = OPMysql()
    round = kwargs.get("round", None)
    id = kwargs.get("id", None)
    order_id = kwargs.get("order_id", None)
    symbol = kwargs.get("symbol", None)
    side = kwargs.get("side", None)
    order_price = kwargs.get("order_price", None)
    order_amount = kwargs.get("order_amount", None)
    done = kwargs.get("done", None)
    sql = "insert into trade_history (round, id, order_id, symbol, side, order_price, order_amount, done) values ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7});"
    while True:
        try:
            res = mysql_client.op_insert(sql.format(round, id, order_id, symbol, side, order_price, order_amount, done))
            if res:
                logger.info("订单：%s 入库成功！" % order_id)
                break
        except:
            time.sleep(1)

def updateOrderInfo(**kwargs):
    '''
    更新一个订单信息
    '''
    mysql_client = OPMysql()
    order_id = kwargs.get("order_id", None)
    order_amount = kwargs.get("order_amount", None)
    done = kwargs.get("done", None)
    sql = "update trade_history set order_amount = {1}, done = {2} where order_id={0};"
    while True:
        try:
            res = mysql_client.op_insert(sql.format(order_id, order_amount, done))
            if res:
                logger.info("订单: %s 更新成功！" % order_id)
                break
        except:
            time.sleep(1)

def delOrderInfo(order_id):
    '''
    删除一个订单信息
    '''
    mysql_client = OPMysql()
    sql = "delete trade_history where order_id = {0};"
    while True:
        try:
            res = mysql_client.op_insert(sql.format(order_id))
            if res:
                logger.info("订单：%s 删除成功！" % order_id)
                break
        except:
            time.sleep(1)


def createFirstOrder():
    '''
    先创建第一个订单，按照市价购买
    '''
    params = {
        'symbol': keys["symbol"],
        'side': 'BUY',
        'type': 'MARKET',
        'quoteOrderQty': keys["first_order_usd"]
    }
    res = client.new_order(**params)
    return res
    
def createLimitOrder(side, quantity, price):
    '''
    创建限价单
    '''
    params = {
        "symbol": keys["symbol"],
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": price
    }
    res = client.new_order(**params)
    return res

def cancelReplaceOrder(order_id, quantity, price):
    '''
    撤销订单并重新下单
    '''
    params = {
            "symbol": keys["symbol"],
            "side": "SELL",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price,
            "cancelReplaceMode": "STOP_ON_FAILURE",
            "cancelOrderId": order_id
        }
    res = client.cancel_and_replace(**params)
    return res

def reCalTakeProfitOrder(round):
    '''
    重新计算止盈单的挂单信息
    '''
    mysql_client = OPMysql()
    sql = "select order_price, order_amount from trade_history where round = {0};"
    res_list = mysql_client.op_select(sql.format(round))
    # 汇总交易所得的btc总量
    total_btc_amount = 0
    # 汇总交易花费的usd总量
    total_usd_amount = 0
    for res in res_list:
        total_btc_amount += res["order_amount"]
        total_usd_amount += res["order_price"] * res["order_amount"]
    # 重新计算卖单价格
    new_sell_price = total_usd_amount * (1 + keys["profit_target"]) / total_btc_amount
    return new_sell_price, total_btc_amount



def canccelOrder(order_id):
    '''
    撤单
    '''
    params = {
            "symbol": keys["symbol"],
            "orderId": order_id
        }
    res = client.cancel_order(**params)
    return res

def getAllOpenOrderId(round):
    '''
    获取所有未成交订单id
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round={} and done=0 and id < 11;"
    res_list =  mysql_client.op_select(sql.format(round))
    return res_list