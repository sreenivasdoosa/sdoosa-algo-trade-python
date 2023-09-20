import logging
import json

from SmartApi.webSocket import WebSocket
from SmartApi import SmartWebSocketV2

from ticker.BaseTicker import BaseTicker
from instruments.Instruments import Instruments
from models.TickData import TickData

class AngelOneTicker(BaseTicker):
  EXCHANGE_TYPE_MAPPING = {'NSE':1,'BSE':3,'NFO':2,'MCX':5,'NCDEX':7,'CDS':13}
  def __init__(self,context):
    super().__init__("angel",context)

  #This is a blocking method call because SmartWebSocketV2.connect() is blocking.
  #So there should not be any statements after this method is called as it would not be called until the control from thcker.connect() method is returned.
  def startTicker(self):
    brokerAppDetails = self.brokerLogin.getBrokerAppDetails()
    accessToken = self.brokerLogin.getBrokerHandle().access_token
    feedToken = self.brokerLogin.getBrokerHandle().feed_token
    if feedToken == None:
      logging.error('[%s] AngelOneTicker startTicker: Cannot start ticker as feedToken is empty', self.context)
      return
    
    ticker = SmartWebSocketV2(accessToken,brokerAppDetails.appKey,brokerAppDetails.clientID,feedToken)
    ticker.on_open = self.on_connect
    ticker.on_close = self.on_close
    ticker.on_error = self.on_error
    ticker.on_data = self.on_ticks
    
    logging.info('[%s] AngelOneTicker: Going to connect..', self.context)
    self.brokerAppDetails = brokerAppDetails
    self.ticker = ticker
    #This is a blocking method call. The control doesn't come back until the connection breaks.
    #ALl the communications happen after this is event driven and are captured on callbacks defined above.
    self.ticker.connect()

  def stopTicker(self):
    logging.info('[%s] AngelOneTicker: stopping..', self.context)
    self.ticker.close_connection()

  def registerSymbols(self, symbols):
    exch_token_map = {'NSE':[],'NFO':[],'BSE':[],'MCX':[],'NCDEX':[],'CDS':[]}
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      exch_seg = isd['exch_seg']
      instrumentToken = isd[self.brokerAppDetails.instrumentKeys.instrumentToken]
      exch_token_map[exch_seg].append(instrumentToken)
      logging.info('[%s] AngelOneTicker registerSymbol: %s token = %s', self.context, symbol, instrumentToken)
      
    messageTokens = self._prepareMessageTokens(exch_token_map)
    logging.info('[%s] AngelOneTicker Subscribing token %s', self.context, messageTokens)
    self.ticker.subscribe(self.context,3,messageTokens)
    
  def unregisterSymbols(self, symbols):
    exch_token_map = {'NSE':[],'NFO':[],'BSE':[],'MCX':[],'NCDEX':[],'CDS':[]}
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      exch_seg = isd['exch_seg']
      instrumentToken = isd[self.brokerAppDetails.instrumentKeys.instrumentToken]
      exch_token_map[exch_seg].append(instrumentToken)
      logging.info('[%s] AngelOneTicker unregisterSymbol: %s token = %s', self.context, symbol, instrumentToken)
      
    messageTokens = self._prepareMessageTokens(exch_token_map)
    logging.info('[%s] AngelOneTicker Unsubscribing token %s', self.context, messageTokens)
    self.ticker.unsubscribe(self.context,3,messageTokens)
    
  def on_ticks(self, ws, bTick):
    logging.info('on_ticks message = %s', bTick)
    # convert broker specific Ticks to our system specific Ticks (models.TickData) and pass to super class function
    ticks = []
    isd = Instruments.getInstrumentDataByToken(bTick['token'])
    tradingSymbol = isd[self.brokerAppDetails.instrumentKeys.tradingSymbol]
    tick = TickData(tradingSymbol)
    tick.lastTradedPrice = bTick['last_traded_price']
    tick.lastTradedQuantity = bTick['last_traded_quantity']
    tick.avgTradedPrice = bTick['average_traded_price']
    tick.volume = bTick['volume_trade_for_the_day']
    tick.totalBuyQuantity = bTick['total_buy_quantity']
    tick.totalSellQuantity = bTick['total_sell_quantity']
    tick.open = bTick['open_price_of_the_day']
    tick.high = bTick['high_price_of_the_day']
    tick.low = bTick['low_price_of_the_day']
    tick.close = bTick['closed_price']
    tick.oi=bTick['open_interest']
    tick.timestamp=bTick['exchange_timestamp']
    #tick.change = bTick['cng']
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

  def _prepareMessageTokens(self, exch_token_map):
    tokens = []
    for key, value in exch_token_map.items():
      if len(value)>0:
        token = { "exchangeType": self.EXCHANGE_TYPE_MAPPING[key], "tokens": value}
        tokens.append(token)
    return tokens