
from core.Controller import Controller

class BaseOrderManager:
  def __init__(self, broker):
    self.broker = broker
    self.brokerHandle = Controller.getBrokerLogin().getBrokerHandle()

  def placeOrder(self, tradingSymbol, price, qty, direction):
    pass

  def modifyOrder(self, orderId, newPrice = 0, newQty = 0):
    pass

  def placeSLOrder(self, tradingSymbol, triggerPrice, qty, direction):
    pass

  def cancelOrder(self, orderId):
    pass
