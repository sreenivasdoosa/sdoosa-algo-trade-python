import logging

from ordermgmt.BaseOrderManager import BaseOrderManager
from ordermgmt.Order import Order

from models.ProductType import ProductType
from models.OrderType import OrderType
from models.Direction import Direction
from models.OrderStatus import OrderStatus

from utils.Utils import Utils

class ZerodhaOrderManager(BaseOrderManager):
  def __init__(self):
    super().__init__("zerodha")

  def placeOrder(self, orderInputParams):
    logging.info('%s: Going to place order with params %s', self.broker, orderInputParams)
    kite = self.brokerHandle
    try:
      orderId = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=kite.EXCHANGE_NFO if orderInputParams.isFnO == True else kite.EXCHANGE_NSE,
        tradingsymbol=orderInputParams.tradingSymbol,
        transaction_type=self.convertToBrokerDirection(orderInputParams.direction),
        quantity=orderInputParams.qty,
        price=orderInputParams.price,
        trigger_price=orderInputParams.triggerPrice,
        product=self.convertToBrokerProductType(orderInputParams.productType),
        order_type=self.convertToBrokerOrderType(orderInputParams.orderType))

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
    kite = self.brokerHandle
    try:
      orderId = kite.modify_order(
        variety=kite.VARIETY_REGULAR,
        order_id=order.orderId,
        quantity=orderModifyParams.newQty if orderModifyParams.newQty > 0 else None,
        price=orderModifyParams.newPrice if orderModifyParams.newPrice > 0 else None,
        trigger_price=orderModifyParams.newTriggerPrice if orderModifyParams.newTriggerPrice > 0 else None,
        order_type=orderModifyParams.newOrderType if orderModifyParams.newOrderType != None else None)

      logging.info('%s Order modified successfully for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrderToMarket(self, order):
    logging.info('%s: Going to modify order with params %s', self.broker)
    kite = self.brokerHandle
    try:
      orderId = kite.modify_order(
        variety=kite.VARIETY_REGULAR,
        order_id=order.orderId,
        order_type=kite.ORDER_TYPE_MARKET)

      logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify to market failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def cancelOrder(self, order):
    logging.info('%s Going to cancel order %s', self.broker, order.orderId)
    kite = self.brokerHandle
    try:
      orderId = kite.cancel_order(
        variety=kite.VARIETY_REGULAR,
        order_id=order.orderId)

      logging.info('%s Order cancelled successfully, orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order cancel failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def fetchAndUpdateAllOrderDetails(self, orders):
    logging.info('%s Going to fetch order book', self.broker)
    kite = self.brokerHandle
    orderBook = None
    try:
      orderBook = kite.orders()
    except Exception as e:
      logging.error('%s Failed to fetch order book', self.broker)
      return

    logging.info('%s Order book length = %d', self.broker, len(orderBook))
    numOrdersUpdated = 0
    for bOrder in orderBook:
      foundOrder = None
      for order in orders:
        if order.orderId == bOrder['order_id']:
          foundOrder = order
          break
      
      if foundOrder != None:
        logging.info('Found order for orderId %s', foundOrder.orderId)
        foundOrder.qty = bOrder['quantity']
        foundOrder.filledQty = bOrder['filled_quantity']
        foundOrder.pendingQty = bOrder['pending_quantity']
        foundOrder.orderStatus = bOrder['status']
        if foundOrder.orderStatus == OrderStatus.CANCELLED and foundOrder.filledQty > 0:
          # Consider this case as completed in our system as we cancel the order with pending qty when strategy stop timestamp reaches
          foundOrder.orderStatus = OrderStatus.COMPLETED
        foundOrder.price = bOrder['price']
        foundOrder.triggerPrice = bOrder['trigger_price']
        foundOrder.averagePrice = bOrder['average_price']
        logging.info('%s Updated order %s', self.broker, foundOrder)
        numOrdersUpdated += 1

    logging.info('%s: %d orders updated with broker order details', self.broker, numOrdersUpdated)

  def convertToBrokerProductType(self, productType):
    kite = self.brokerHandle
    if productType == ProductType.MIS:
      return kite.PRODUCT_MIS
    elif productType == ProductType.NRML:
      return kite.PRODUCT_NRML
    elif productType == ProductType.CNC:
      return kite.PRODUCT_CNC
    return None 

  def convertToBrokerOrderType(self, orderType):
    kite = self.brokerHandle
    if orderType == OrderType.LIMIT:
      return kite.ORDER_TYPE_LIMIT
    elif orderType == OrderType.MARKET:
      return kite.ORDER_TYPE_MARKET
    elif orderType == OrderType.SL_MARKET:
      return kite.ORDER_TYPE_SLM
    elif orderType == OrderType.SL_LIMIT:
      return kite.ORDER_TYPE_SL
    return None

  def convertToBrokerDirection(self, direction):
    kite = self.brokerHandle
    if direction == Direction.LONG:
      return kite.TRANSACTION_TYPE_BUY
    elif direction == Direction.SHORT:
      return kite.TRANSACTION_TYPE_SELL
    return None
