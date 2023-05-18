import logging
import json

from smartapi.webSocket import WebSocket
from smartapi import SmartWebSocketV2

from ticker.BaseTicker import BaseTicker
from instruments.Instruments import Instruments
from models.TickData import TickData

class AngelOneTicker(BaseTicker):
  EXCHANGE_TYPE_MAPPING = {'NSE':1,'BSE':3,'NFO':2,'MCX':5,'NCDEX':7,'CDS':13}
  def __init__(self):
    super().__init__("angel")

  def startTicker(self):
    brokerAppDetails = self.brokerLogin.getBrokerAppDetails()
    feedToken = self.brokerLogin.getBrokerHandle().feed_token
    if feedToken == None:
      logging.error('AngelOneTicker startTicker: Cannot start ticker as feedToken is empty')
      return
    
    ticker = SmartWebSocketV2(brokerAppDetails.clientID,feedToken)
    ticker.on_open = self.on_connect
    ticker.on_close = self.on_close
    ticker.on_error = self.on_error
    ticker.on_data = self.on_ticks
    
    logging.info('AngelOneTicker: Going to connect..')
    self.brokerAppDetails = brokerAppDetails
    self.ticker = ticker
    self.ticker.connect()

  def stopTicker(self):
    logging.info('AngelOneTicker: stopping..')
    self.ticker.close_connection()

  def registerSymbols(self, symbols):
    exch_token_map = {'NSE':[],'NFO':[],'BSE':[],'MCX':[],'NCDEX':[],'CDS':[]}
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      exch_seg = isd['exch_seg']
      instrumentToken = isd[self.brokerAppDetails.instrumentKeys.instrumentToken]
      exch_token_map[exch_seg].append(instrumentToken)
      logging.info('AngelOneTicker registerSymbol: %s token = %s', symbol, instrumentToken)
      
    messageTokens = self._prepareMessageTokens(exch_token_map)
    logging.info('AngelOneTicker Subscribing token %s', messageTokens)
    self.ticker.subscribe('zeel_123_free',3,messageTokens)
    
  def unregisterSymbols(self, symbols):
    exch_token_map = {'NSE':[],'NFO':[],'BSE':[],'MCX':[],'NCDEX':[],'CDS':[]}
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      exch_seg = isd['exch_seg']
      instrumentToken = isd[self.brokerAppDetails.instrumentKeys.instrumentToken]
      exch_token_map[exch_seg].append(instrumentToken)
      logging.info('AngelOneTicker unregisterSymbol: %s token = %s', symbol, instrumentToken)
      
    messageTokens = self._prepareMessageTokens(exch_token_map)
    logging.info('AngelOneTicker Unsubscribing token %s', messageTokens)
    self.ticker.unsubscribe('zeel_123_free',3,messageTokens)
    
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