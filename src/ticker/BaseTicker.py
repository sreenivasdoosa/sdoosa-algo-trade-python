import logging

from core.Controller import Controller

class BaseTicker:
  def __init__(self, broker):
    self.broker = broker
    self.brokerLogin = Controller.getBrokerLogin()
    self.ticker = None
    self.tickListeners = []

  def startTicker(self):
    pass

  def stopTicker(self):
    pass

  def registerListener(self, listener):
    # All registered tick listeners will be notified on new ticks
    self.tickListeners.append(listener)

  def registerSymbols(self, symbols):
    pass

  def unregisterSymbols(self, symbols):
    pass

  def onNewTicks(self, ticks):
    # logging.info('New ticks received %s', ticks)
    for tick in ticks:
      for listener in self.tickListeners:
        try:
          listener(tick)
        except Exception as e:
          logging.error('BaseTicker: Exception from listener callback function. Error => %s', str(e))

  def onConnect(self):
    logging.info('Ticker connection successful.')

  def onDisconnect(self, code, reason):
    logging.error('Ticker got disconnected. code = %d, reason = %s', code, reason)

  def onError(self, code, reason):
    logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

  def onReconnect(self, attemptsCount):
    logging.warn('Ticker reconnecting.. attemptsCount = %d', attemptsCount)

  def onMaxReconnectsAttempt(self):
    logging.error('Ticker max auto reconnects attempted and giving up..')

  def onOrderUpdate(self, data):
    #logging.info('Ticker: order update %s', data)
    pass
