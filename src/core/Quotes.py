
from core.Controller import Controller

class Quotes:
  @staticmethod
  def getCMP(tradingSymbol):
    brokerLogin = Controller.getBrokerLogin()
    brokerHandle = brokerLogin.getBrokerHandle()
    quote = None
    if brokerLogin.broker == "zerodha":
      quote = brokerHandle.quote(tradingSymbol)
      if quote:
        return quote[tradingSymbol]['last_price']
      else:
        return 0
    else:
      # The logic may be different for other brokers
      return 0
