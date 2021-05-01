
class BaseLogin:

  def __init__(self, brokerAppDetails):
    self.brokerAppDetails = brokerAppDetails
    self.broker = brokerAppDetails.broker

  # Derived class should implement login function and return redirect url
  def login(self, args):
    pass

  def setBrokerHandle(self, brokerHandle):
    self.brokerHandle = brokerHandle

  def setAccessToken(self, accessToken):
    self.accessToken = accessToken

  def getBrokerAppDetails(self):
    return self.brokerAppDetails

  def getAccessToken(self):
    return self.accessToken

  def getBrokerHandle(self):
    return self.brokerHandle