import logging
import json

from smartapi.webSocket import WebSocket
from smartapi import SmartWebSocket

from ticker.BaseTicker import BaseTicker
from instruments.Instruments import Instruments
from models.TickData import TickData

class AngelOneTicker(BaseTicker):
  EXCHANGE_MAPPING = {'NSE':'nse_cm','BSE':'bse_cm','NFO':'nse_fo','MCX':'mcx_fo','NCDEX':'nce_fo','CDS':'cde_fo'}
  def __init__(self):
    super().__init__("angel")

  def startTicker(self):
    brokerAppDetails = self.brokerLogin.getBrokerAppDetails()
    feedToken = self.brokerLogin.getBrokerHandle().feed_token
    if feedToken == None:
      logging.error('AngelOneTicker startTicker: Cannot start ticker as feedToken is empty')
      return
    
    ticker = SmartWebSocket(feedToken, brokerAppDetails.clientID)
    ticker._on_open = self.on_connect
    ticker._on_close = self.on_close
    ticker._on_error = self.on_error
    ticker._on_message = self.on_ticks
    
    #ticker = WebSocket(feedToken, brokerAppDetails.clientID,debug=True)
    #ticker.on_connect = self.on_connect
    #ticker.on_close = self.on_close
    #ticker.on_error = self.on_error
    #ticker.on_reconnect = self.on_reconnect
    #ticker.on_noreconnect = self.on_noreconnect
    #ticker.on_ticks = self.on_ticks

    logging.info('AngelOneTicker: Going to connect..')
    self.brokerAppDetails = brokerAppDetails
    self.ticker = ticker
    self.ticker.connect()
    #self.ticker.connect(threaded=True,disable_ssl_verification=True)

  def stopTicker(self):
    logging.info('AngelOneTicker: stopping..')
    self.ticker.close(1000, "Manual close")

  def registerSymbols(self, symbols):
    tokens = []
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      token = self._prepareMessageToken(isd)
      logging.info('AngelOneTicker registerSymbol: %s token = %s', symbol, token)
      tokens.append(token)

    messageTokens = "&".join(f'"{s}"' for s in tokens)
    logging.info('AngelOneTicker Subscribing token %s', messageTokens)
    self.ticker.subscribe('mw',messageTokens)
    #self.ticker.send_request(messageTokens,'mw')

  def unregisterSymbols(self, symbols):
    tokens = []
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      token = self._prepareMessageToken(isd)
      logging.info('AngelOneTicker unregisterSymbols: %s token = %s', symbol, token)
      tokens.append(token)

    messageTokens = "&".join(f'"{s}"' for s in tokens)
    logging.info('AngelOneTicker Unsubscribing tokens %s', messageTokens)
    self.ticker.subscribe('mw',messageTokens)
    #self.ticker.send_request(messageTokens,'mw')

  def on_ticks(self, ws, brokerTicks):
    logging.info('on_ticks message = %s', brokerTicks)
    # convert broker specific Ticks to our system specific Ticks (models.TickData) and pass to super class function
    ticks = []
    for bTick in brokerTicks:
      if 'ts' in bTick:
        tradingSymbol = bTick['ts']
        tick = TickData(tradingSymbol)
        tick.lastTradedPrice = bTick['ltp']
        tick.lastTradedQuantity = bTick['ltq']
        tick.avgTradedPrice = bTick['ap']
        tick.volume = bTick['v']
        tick.totalBuyQuantity = bTick['tbq']
        tick.totalSellQuantity = bTick['tsq']
        tick.open = bTick['op']
        tick.high = bTick['h']
        tick.low = bTick['lo']
        tick.close = bTick['c']
        tick.change = bTick['cng']
        ticks.append(tick)
      
    self.onNewTicks(ticks)

  def on_connect(self, ws):
    self.onConnect()

  def on_close(self, ws):
    self.onDisconnect(0, "disconnected")

  def on_error(self, ws, error):
    self.onError(0, "error")

  def on_reconnect(self, ws, attemptsCount):
    self.onReconnect(attemptsCount)

  def on_noreconnect(self, ws):
    self.onMaxReconnectsAttempt()

  def on_order_update(self, ws, data):
    self.onOrderUpdate(data)

  def _prepareMessageToken(self, instrument):
    return self._getExchangeMapping(instrument['exch_seg'])+"|"+instrument[self.brokerAppDetails.instrumentKeys.instrumentToken]

  def _getExchangeMapping(self, exchange):
    return self.EXCHANGE_MAPPING[exchange]