
class OrderModifyParams:
  def __init__(self):
    self.newPrice = 0
    self.newTriggerPrice = 0 # Applicable in case of SL order
    self.newQty = 0
    self.newOrderType = None # Ex: Can change LIMIT order to SL order or vice versa. Not supported by all brokers

  def __str__(self):
    return + "newPrice=" + str(self.newPrice) + ", newTriggerPrice=" + str(self.newTriggerPrice) \
      + ", newQty=" + str(self.newQty) + ", newOrderType=" + str(self.newOrderType)
      