
class Order:
  def __init__(self):
    self.tradingSymbol = None
    self.exchange = "NSE"
    self.productType = None # MIS/NRML/CNC
    self.orderId = None # The order id received from broker after placing the order
    self.orderStatus = None # One of the status defined in ordermgmt.OrderStatus
    self.orderType = # LIMIT/MARKET/SL-LIMIT/SL-MARKET
    self.price = 0
    self.triggerPrice = 0 # Applicable in case of SL orders
    self.averagePrice = 0 # Average price at which the order is filled
    self.qty = 0
    self.filledQty = 0 # Filled quantity
    self.pendingQty = # Qty - Filled quantity
    self.orderPlaceTimestamp = None # Timestamp when the order is placed
    self.lastOrderUpdateTimestamp = None # Applicable if you modify the order Ex: Trailing SL
    

