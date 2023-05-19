import logging

from ordermgmt.BaseOrderManager import BaseOrderManager
from ordermgmt.Order import Order

from models.ProductType import ProductType
from models.OrderType import OrderType
from models.Direction import Direction
from models.OrderStatus import OrderStatus

from utils.Utils import Utils

class AngelOneOrderManager(BaseOrderManager):
  def __init__(self):
    super().__init__("angel")

  def placeOrder(self, orderInputParams):
    logging.info('%s: Going to place order with params %s', self.broker, orderInputParams)
    smartConnect = self.brokerHandle
    try:
      orderId = smartConnect.placeOrder({
        'variety':'NORMAL',
        'exchange':'NFO' if orderInputParams.isFnO == True else 'NSE',
        'tradingsymbol':orderInputParams.tradingSymbol,
        'transactiontype':self.convertToBrokerDirection(orderInputParams.direction),
        'quantity':orderInputParams.qty,
        'price':orderInputParams.price,
        'triggerprice':orderInputParams.triggerPrice,
        'producttype':self.convertToBrokerProductType(orderInputParams.productType),
        'ordertype':self.convertToBrokerOrderType(orderInputParams.orderType)
        })

      logging.info('%s: Order placed successfully, orderId = %s', self.broker, orderId)
      order = Order(orderInputParams)
      order.orderId = orderId
      order.orderPlaceTimestamp = Utils.getEpoch()
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order placement failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrder(self, order, orderModifyParams):
    logging.info('%s: Going to modify order with params %s', self.broker, orderModifyParams)
    smartConnect = self.brokerHandle
    try:
      orderId = smartConnect.modifyOrder({
        'variety':'NORMAL',
        'orderid':order.orderId,
        'quantity':orderModifyParams.newQty if orderModifyParams.newQty > 0 else None,
        'price':orderModifyParams.newPrice if orderModifyParams.newPrice > 0 else None,
        'triggerprice':orderModifyParams.newTriggerPrice if orderModifyParams.newTriggerPrice > 0 else None,
        'ordertype':orderModifyParams.newOrderType if orderModifyParams.newOrderType != None else None
        })

      logging.info('%s Order modified successfully for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrderToMarket(self, order):
    logging.info('%s: Going to modify order with params %s', self.broker)
    smartConnect = self.brokerHandle
    try:
      orderId = smartConnect.modifyOrder({
        'variety':'NORMAL',
        'orderid':order.orderId,
        'ordertype':'MARKET'
        })['data']['orderid']

      logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify to market failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def cancelOrder(self, order):
    logging.info('%s Going to cancel order %s', self.broker, order.orderId)
    smartConnect = self.brokerHandle
    try:
      orderId = smartConnect.cancelOrder({
        'variety':'NORMAL',
        'orderid':order.orderId
        })['data']['orderid']

      logging.info('%s Order cancelled successfully, orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order cancel failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def fetchAndUpdateAllOrderDetails(self, orders):
    logging.info('%s Going to fetch order book', self.broker)
    smartConnect = self.brokerHandle
    orderBook = None
    try:
      orderBook = smartConnect.orderBook()
    except Exception as e:
      logging.error('%s Failed to fetch order book', self.broker)
      return

    logging.info('%s Order book length = %d', self.broker, len(orderBook))
    numOrdersUpdated = 0
    for bOrder in orderBook['data']:
      foundOrder = None
      for order in orders:
        if order.orderId == bOrder['orderid']:
          foundOrder = order
          break
      
      if foundOrder != None:
        logging.info('Found order for orderId %s', foundOrder.orderId)
        foundOrder.qty = bOrder['quantity']
        foundOrder.filledQty = bOrder['filledshares']
        foundOrder.pendingQty = bOrder['unfilledshares']
        foundOrder.orderStatus = bOrder['orderstatus']
        if foundOrder.orderStatus == OrderStatus.CANCELLED and foundOrder.filledQty > 0:
          # Consider this case as completed in our system as we cancel the order with pending qty when strategy stop timestamp reaches
          foundOrder.orderStatus = OrderStatus.COMPLETED
        foundOrder.price = bOrder['price']
        foundOrder.triggerPrice = bOrder['triggerprice']
        foundOrder.averagePrice = bOrder['averageprice']
        logging.info('%s Updated order %s', self.broker, foundOrder)
        numOrdersUpdated += 1

    logging.info('%s: %d orders updated with broker order details', self.broker, numOrdersUpdated)

  def convertToBrokerProductType(self, productType):
    if productType == ProductType.MIS:
      return 'INTRADAY'
    elif productType == ProductType.NRML:
      return 'CARRYFORWARD'
    elif productType == ProductType.CNC:
      return 'DELIVERY'
    return None 

  def convertToBrokerOrderType(self, orderType):
    if orderType == OrderType.LIMIT:
      return 'LIMIT'
    elif orderType == OrderType.MARKET:
      return 'MARKET'
    elif orderType == OrderType.SL_MARKET:
      return 'STOPLOSS_MARKET'
    elif orderType == OrderType.SL_LIMIT:
      return 'STOPLOSS_LIMIT'
    return None

  def convertToBrokerDirection(self, direction):
    kite = self.brokerHandle
    if direction == Direction.LONG:
      return 'BUY'
    elif direction == Direction.SHORT:
      return 'SELL'
    return None
