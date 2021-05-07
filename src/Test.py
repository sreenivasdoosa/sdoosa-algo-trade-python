import logging
import time

from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.Order import Order
from core.Quotes import Quotes
from utils.Utils import Utils

class Test:
  def testTicker():
    ticker = ZerodhaTicker()
    ticker.startTicker()
    ticker.registerListener(Test.tickerListener)

    # sleep for 5 seconds and register trading symbols to receive ticks
    time.sleep(5)
    ticker.registerSymbols(['SBIN', 'RELIANCE'])

    # wait for 60 seconds and stop ticker service
    time.sleep(60)
    logging.info('Going to stop ticker')
    ticker.stopTicker()

  def tickerListener(tick):
    logging.info('tickerLister: onNewTick %s', vars(tick));

  def testOrders():
    orderManager = ZerodhaOrderManager()
    exchange = 'NSE';
    tradingSymbol = 'SBIN'
    lastTradedPrice = Quotes.getCMP(exchange + ':' + tradingSymbol)
    logging.info(tradingSymbol + ' CMP = %f', lastTradedPrice)

    limitPrice = lastTradedPrice - lastTradedPrice * 1 / 100
    limitPrice = Utils.roundToNSEPrice(limitPrice)
    qty = 1
    direction = 'LONG'

    # place order
    origOrderId = orderManager.placeOrder(tradingSymbol, limitPrice, qty, direction)
    logging.info('Original order Id %s', origOrderId)

    # sleep for 10 seconds then modify order
    time.sleep(10)
    newPrice = lastTradedPrice
    if origOrderId:
        orderManager.modifyOrder(origOrderId, newPrice)

    # sleep for 10 seconds and then place SL order
    time.sleep(10)
    slPrice = newPrice - newPrice * 1 / 100
    slPrice = Utils.roundToNSEPrice(slPrice)
    slDirection = 'SHORT' if direction == 'LONG' else 'LONG'
    slOrderId = orderManager.placeSLOrder(tradingSymbol, slPrice, qty, slDirection)
    logging.info('SL order Id %s', slOrderId)

    # sleep for 10 seconds and then place target order
    time.sleep(10)
    targetPrice = newPrice + newPrice * 2 / 100
    targetPrice = Utils.roundToNSEPrice(targetPrice)
    targetDirection = 'SHORT' if direction == 'LONG' else 'LONG'
    targetOrderId = orderManager.placeOrder(tradingSymbol, targetPrice, qty, targetDirection)
    logging.info('Target order Id %s', targetOrderId)

    # sleep for 10 seconds and cancel target order
    time.sleep(10)
    if targetOrderId:
        orderManager.cancelOrder(targetOrderId)
        logging.info('Cancelled Target order Id %s', targetOrderId)

    logging.info("Algo done executing all orders. Check ur orders and positions in broker terminal.") 

  def testMisc():
    orderManager = ZerodhaOrderManager()
    sampleOrder = Order(orderInputParams=None)
    sampleOrder.orderId='210505200078243'
    orders = []
    orders.append(sampleOrder)
    orderManager.fetchAndUpdateAllOrderDetails(orders)