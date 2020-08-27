from zerodha import getKite
import logging

# Supported Order types by kite
# ORDER_TYPE_MARKET = "MARKET"
# ORDER_TYPE_LIMIT = "LIMIT"
# ORDER_TYPE_SLM = "SL-M"
# ORDER_TYPE_SL = "SL"

def placeOrder(tradingSymbol, price, qty, direction):
  logging.info('Going to place order %s %f %d %s', tradingSymbol, price, qty, direction)
  kite = getKite()
  try:
    orderId = kite.place_order(
      variety=kite.VARIETY_REGULAR,
      exchange=kite.EXCHANGE_NSE,
      tradingsymbol=tradingSymbol,
      transaction_type=kite.TRANSACTION_TYPE_BUY if direction == 'LONG' else kite.TRANSACTION_TYPE_SELL,
      quantity=qty,
      price=price,
      product=kite.PRODUCT_MIS,
      order_type=kite.ORDER_TYPE_LIMIT)

    logging.info('Order placed successfully, orderId = %s', orderId)
    return orderId
  except Exception as e:
    logging.info('Order placement failed: %s', e.message)


def modifyOrder(orderId, newPrice = 0, newQty = 0):
  logging.info('Going to modify order %s %f %d', orderId, newPrice, newQty)
  kite = getKite()
  try:
    orderId = kite.modify_order(
      variety=kite.VARIETY_REGULAR,
      order_id=orderId,
      quantity=newQty if newQty > 0 else None,
      price=newPrice if newPrice > 0 else None)

    logging.info('Order modified successfully, orderId = %s', orderId)
    return orderId
  except Exception as e:
    logging.info('Order modify failed: %s', e.message)


def placeSLOrder(tradingSymbol, triggerPrice, qty, direction):
  logging.info('Going to place SL order %s %f %d %s', tradingSymbol, triggerPrice, qty, direction)
  kite = getKite()
  try:
    orderId = kite.place_order(
      variety=kite.VARIETY_REGULAR,
      exchange=kite.EXCHANGE_NSE,
      tradingsymbol=tradingSymbol,
      transaction_type=kite.TRANSACTION_TYPE_BUY if direction == 'LONG' else kite.TRANSACTION_TYPE_SELL,
      quantity=qty,
      trigger_price=triggerPrice,
      product=kite.PRODUCT_MIS,
      order_type=kite.ORDER_TYPE_SLM)

    logging.info('SL Order placed successfully, orderId = %s', orderId)
    return orderId
  except Exception as e:
    logging.info('SL Order placement failed: %s', e.message)

def cancelOrder(orderId):
  logging.info('Going to cancel order %s', orderId)
  kite = getKite()
  try:
    orderId = kite.cancel_order(
      variety=kite.VARIETY_REGULAR,
      order_id=orderId)

    logging.info('Order cancelled successfully, orderId = %s', orderId)
    return orderId
  except Exception as e:
    logging.info('Order cancel failed: %s', e.message)