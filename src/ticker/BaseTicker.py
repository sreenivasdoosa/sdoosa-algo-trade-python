import logging

from core.Controller import Controller

class BaseTicker:
  def __init__(self, broker, context):
    self.broker = broker
    self.brokerLogin = Controller.getBrokerLogin()
    self.ticker = None
    self.tickListeners = []
    self.connectionListeners = []
    self.context = context

  def startTicker(self):
    pass

  def stopTicker(self):
    pass

  def registerListener(self, listener):
    # All registered tick listeners will be notified on new ticks
    self.tickListeners.append(listener)

  def registerConnectionListener(self, listener):
    # All registered connection listeners will be notified on connect
    self.connectionListeners.append(listener)

  def registerSymbols(self, symbols):
    pass

  def unregisterSymbols(self, symbols):
    pass

  def onNewTicks(self, ticks):
    #logging.info('in onNewTicks: new Ticks received %s size of listeners %d', ticks,len(self.tickListeners))
    for tick in ticks:
      for listener in self.tickListeners:
        try:
          listener(tick)
        except Exception as e:
          logging.error('[%s] BaseTicker: Exception from listener callback function. Error => %s', self.context, str(e))

  def onConnect(self):
    logging.info('[%s] Ticker connection successful.', self.context)
    for listener in self.connectionListeners:
        try:
          listener()
        except Exception as e:
          logging.error('[%s] BaseTicker: Exception from listener callback function. Error => %s', self.context, str(e))

  def onDisconnect(self, code, reason):
    logging.error('[%s] Ticker got disconnected. code = %d, reason = %s', self.context, code, reason)

  def onError(self, code, reason):
    logging.error('[%s] Ticker errored out. code = %d, reason = %s', self.context, code, reason)

  def onReconnect(self, attemptsCount):
    logging.warn('[%s] Ticker reconnecting.. attemptsCount = %d', self.context, attemptsCount)

  def onMaxReconnectsAttempt(self):
    logging.error('[%s] Ticker max auto reconnects attempted and giving up..', self.context)

  def onOrderUpdate(self, data):
    #logging.info('Ticker: order update %s', data)
    pass
