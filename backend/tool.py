from .mysqlConnect import OPMysql
from config import client
from config import redis_conn
from config import logger
import time
from config import keys


def getRoundStatus(count):
    '''
    根据传入的count,查询当前count的订单状态是否已完成
    返回1, 表示当前count还在运行。
    返回0, 表示当前count已结束。
    '''
    mysql_client = OPMysql()
    sql = "SELECT order_id from trade_history where round={0} and done=0;"
    res = mysql_client.op_select(sql.format(count))
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
    if redis_conn.exists("count"):
        count = int(redis_conn.get("count").decode("utf8"))
    else:
        count = 0
    return count

def setRound(count):
    '''
    设置策略交易编号
    '''
    try:
        redis_conn.set("count", count)
        logger.info("设置count为{0}".format(count))
    except:
        logger.info("设置count为{0}失败".format(count))


def setLatestOpenBuyOrderId(count):
    '''
    将最新未成交买单塞进redis
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round={} and done=0 and id < 11 order by id asc limit 1;"
    res_list =  mysql_client.op_select(sql.format(count))
    # 如果结果为空
    if len(res_list) == 0:
        redis_conn.set("latest:open:buy:order_id", 0)
    else:
        order_id = res_list[0]["order_id"]
        redis_conn.set("latest:open:buy:order_id", order_id)
        logger.info("设置最新未成交订单id: {0}".format(order_id))

def getLatestOpenBuyOrderId():
    order_id = redis_conn.get("latest:open:buy:order_id").decode("utf8")
    return order_id


def getSellOrderId(count):
    '''
    获取卖单的订单id
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round = {0} and id = 11;"
    res = mysql_client.op_select(sql.format(count))
    return res[0].get("order_id",None)

def setOrderInfo(**kwargs):
    '''
    将订单信息入库
    '''
    mysql_client = OPMysql()
    count = kwargs.get("count", 'NULL')
    id = kwargs.get("id", 'NULL')
    order_id = kwargs.get("order_id", 'NULL')
    symbol = kwargs.get("symbol", 'NULL')
    side = kwargs.get("side", 'NULL')
    order_price = kwargs.get("order_price", 'NULL')
    order_amount = kwargs.get("order_amount", 'NULL')
    done = kwargs.get("done", 0)
    sql = "insert into trade_history (`round`, `id`, `order_id`, `symbol`, `side`, `order_price`, `order_amount`, `done`) values ({0}, {1}, {2}, '{3}', {4}, {5}, {6}, {7});"
    while True:
        try:
            logger.info(sql.format(count, id, order_id, symbol, side, order_price, order_amount, done))
            res = mysql_client.op_insert(sql.format(count, id, order_id, symbol, side, order_price, order_amount, done))
            if res:
                logger.info("订单：%s 入库成功！" % order_id)
                break
        except Exception as e:
            logger.exception(e)
            time.sleep(1)

def updateOrderInfo(**kwargs):
    '''
    更新一个订单信息
    '''
    mysql_client = OPMysql()
    order_id = kwargs.get("order_id", 'NULL')
    order_amount = kwargs.get("order_amount", 'NULL')
    done = kwargs.get("done", 'NULL')
    sql = "update trade_history set order_amount = {1}, done = {2} where order_id={0};"
    while True:
        try:
            mysql_client.op_insert(sql.format(order_id, order_amount, done))
            logger.info("订单: %s 更新成功！" % order_id)
            break
        except Exception as e:
            logger.exception(e)
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
    # 撤销订单
    while True:
        res = getOrderStatus(order_id)
        if res["status"] == "FILLED":
            break
        else:
            canccelOrder(order_id)
    
    # 重新下单
    res = createLimitOrder(1, quantity, price)
    return res

def reCalTakeProfitOrder(count):
    '''
    重新计算止盈单的挂单信息
    '''
    mysql_client = OPMysql()
    sql = "select order_price, order_amount from trade_history where round = {0} and done = 1 and side = 0;"
    res_list = mysql_client.op_select(sql.format(count))
    # 汇总交易所得的btc总量
    total_btc_amount = 0
    # 汇总交易花费的usd总量
    total_usd_amount = 0
    for res in res_list:
        total_btc_amount += res["order_amount"]
        total_usd_amount += res["order_price"] * res["order_amount"]
    # 重新计算卖单价格
    new_sell_price = total_usd_amount * (1 + keys["profit_target"]) / total_btc_amount
    return round(new_sell_price,2), round(total_btc_amount,4)



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

def getAllOpenOrderId(count):
    '''
    获取所有未成交订单id
    '''
    mysql_client = OPMysql()
    sql = "select order_id from trade_history where round={} and done=0 and id < 11;"
    res_list =  mysql_client.op_select(sql.format(count))
    return res_list


def cancelOpenOrders(symbol):
    params = {
            "symbol": keys["symbol"]
        }
    res = client.cancel_open_orders(**params)
    return res

def getOpenOrders(symbol):
    params = {
            "symbol": keys["symbol"]
        }
    res = client.get_open_orders(**params)
    return res