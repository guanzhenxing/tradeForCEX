
from config import keys
from config import logger
from backend.tool import getRoundStatus
from backend.tool import getOrderStatus
from backend.tool import getRound
from backend.tool import setRound
from backend.tool import setOrderInfo
from backend.tool import createFirstOrder
from backend.tool import createLimitOrder
from backend.tool import getLatestOpenBuyOrderId
from backend.tool import setLatestOpenBuyOrderId
from backend.tool import updateOrderInfo
from backend.tool import reCalTakeProfitOrder
from backend.tool import cancelReplaceOrder
from backend.tool import getSellOrderId
from backend.tool import delOrderInfo
from backend.tool import canccelOrder
from backend.tool import getAllOpenOrderId
from backend.tool import cancelOpenOrders
from backend.tool import getOpenOrders
from multiprocessing import Process
import time
import math


def checkLatestOpenBuyOder():
    '''
    循环检查最近买单是否成交，如果成交，则重新计算卖单的数量和价格，最后更新未成交买单id
    '''
    while True:
        try:
            order_id = getLatestOpenBuyOrderId()
            if order_id == "0":
                time.sleep(5)
                continue
            res = getOrderStatus(order_id)
            if res["status"] == "FILLED":
                # 获得btc数量
                executedQty = res["executedQty"]
                order_info = {"order_id": order_id, "order_amount": executedQty, "done": 1}
                # 更新订单信息
                updateOrderInfo(**order_info)
                # 重新计算止盈单订单信息
                logger.info("1")
                count = getRound()
                new_price, new_quantity = reCalTakeProfitOrder(count)
                # 撤销订单并重新下单
                sell_order_id = getSellOrderId(count)
                res = cancelReplaceOrder(sell_order_id, new_quantity, new_price)
                # 撤销订单并重新下单成功
                new_sell_order_id = res["orderId"]
                delOrderInfo(sell_order_id)
                new_order_info = {"count": count, "id": 11, "order_id": new_sell_order_id, "symbol": keys["symbol"], "side": 1, "order_price": new_price, "done": 0}
                setOrderInfo(**new_order_info)
                logger.info("止盈单更新成功！")
                # 更新最新未成交订单
                setLatestOpenBuyOrderId(count)
        except Exception as e:
            logger.exception(e)
        time.sleep(5)

            

def checkOpenSellOder():
    '''
    循环检查卖单是否成交
    如果成交，
       1) 将本轮次所有买单全部撤单，本轮策略交易结束
       2) 开启下一轮策略交易
    '''
    while True:
        try:
            count = getRound()
            if count:
                sell_order_id = getSellOrderId(count)
                if sell_order_id is not None:
                    res = getOrderStatus(sell_order_id)
                    if res["status"] == "FILLED":
                        executedQty = res["executedQty"]
                        order_info = {"order_id": sell_order_id, "order_amount": executedQty, "done": 1}
                        # 更新订单信息
                        updateOrderInfo(**order_info)
                        # 获取所有未成交订单id
                        res_list = getAllOpenOrderId(count)
                        for res in res_list:
                            # 撤单
                            r = canccelOrder(res["order_id"])
                            logger.info("撤销订单id: {0}".format(res["order_id"]))
                            # 删除订单
                            delOrderInfo(res["order_id"])
                            time.sleep(1)
                        # 开启新一轮策略
                        startRound(count+1)
                        logger.info("开启第{0}轮策略！".format(count+1))
        except Exception as e:
            logger.exception(e)
        time.sleep(5)

def startRound(count):
    '''
    开启新的一轮策略
    '''
    # 设置轮次
    setRound(count)
    # 创建第一个市价单
    res = createFirstOrder()
    status = res["status"]
    first_order_id = res["orderId"]
    # 循环检测，直到市价单完全成交
    while True:
        if status == "FILLED":
            break
        else:
            res = getOrderStatus(first_order_id)
            status = res["status"]
        time.sleep(1)
    # 平均市价价格 = 交易的busd数量 / 获得的btc数量
    cummulativeQuoteQty = res["cummulativeQuoteQty"]
    executedQty = res["executedQty"]
    # 交易的BTC平均价格
    avg_price = float(cummulativeQuoteQty) / float(executedQty)
    # 首次订单id为0
    order_info = {"count": count, "id": 0, "order_id": first_order_id, "symbol": keys["symbol"], "side": 0, "order_price": round(avg_price,2), "order_amount": round(float(executedQty),4), "done": 1}
    setOrderInfo(**order_info)

    # 开始生成加仓单
    times = 1
    total_buy_order_busd_amount = float(cummulativeQuoteQty)
    order_price = avg_price
    while times <= 10:
        buy_order_usd_amount = float(keys["first_order_usd"]) * math.pow(keys["multiplier_of_position_increase_amount"], count - 1)
        quantity = buy_order_usd_amount / (order_price * (1 - keys["down_how_much_to_add_to_the_position"]))
        order_price = order_price * (1 - keys["down_how_much_to_add_to_the_position"])
        # 将所有买单金额相加，如果超过限制，则不在下单
        total_buy_order_busd_amount += buy_order_usd_amount
        if total_buy_order_busd_amount > keys["limit_usd"]:
            break
        res = createLimitOrder("BUY", round(quantity,4), round(order_price,2))
        logger.info("挂一个加仓单, 返回信息: {0}".format(res))
        order_info = {"count": count, "id": times, "order_id": res["orderId"], "symbol": keys["symbol"], "side": 0, "order_price": round(order_price,2), "done": 0}
        setOrderInfo(**order_info)
        times += 1
    
    # 开始生成止盈单
    sell_price = avg_price * (1 + keys["profit_target"])
    sell_quantity = float(executedQty)
    res = createLimitOrder("SELL", round(sell_quantity,4), round(sell_price,2))
    logger.info("挂一个止盈单, 返回信息: {0}".format(res))
    # 止盈单的id为11
    order_info = {"count": count, "id": 11, "order_id": res["orderId"], "symbol": keys["symbol"], "side": 1, "order_price": round(sell_price,2), "done": 0}
    setOrderInfo(**order_info)

    # 设置最新未成交订单
    setLatestOpenBuyOrderId(count)
    
    
    

def main():
    '''
    开启机器人时，检查是否已经有策略在运行，
    如果有，判断是否已经运行完毕，
         1) 运行完毕就开启新一轮
         2) 还在运行则跳过
    如果没有，则开启新一轮策略
    '''
    count = getRound()
    if count > 0:
        count_running = getRoundStatus(count)
        if not count_running:
            new_count = int(count) + 1
            startRound(new_count)
    else:
        startRound(1)


if __name__ == "__main__":
    logger.info("量化机器人启动！")
    main()
    p1 = Process(target=checkLatestOpenBuyOder)
    p1.start()
    logger.info("检测最新买单成交！")
    p2 = Process(target=checkOpenSellOder)
    p2.start()
    logger.info("检测止盈订单成交！")
    # res = cancelOpenOrders(keys["symbol"])
    # logger.info(res)
    # res = getOpenOrders(keys["symbol"])
    # logger.info(res)
    # res =  getOrderStatus(3843464)
    # logger.info(res)
    