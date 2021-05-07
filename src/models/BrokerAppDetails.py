

class BrokerAppDetails:
  def __init__(self, broker):
    self.broker = broker
    self.appKey = None
    self.appSecret = None

  def setClientID(self, clientID):
    self.clientID = clientID

  def setAppKey(self, appKey):
    self.appKey = appKey

  def setAppSecret(self, appSecret):
    self.appSecret = appSecret

