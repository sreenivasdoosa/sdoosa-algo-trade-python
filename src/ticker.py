import logging
import json
from kiteconnect import KiteTicker
from config import getUserConfig
from zerodha import getAccessToken
from instruments import getInstrumentDataBySymbol, getInstrumentDataByToken

ticker = None

def startTicker():
  userConfig = getUserConfig()
  accessToken = getAccessToken()
  if accessToken == None:
    logging.error('startTicker: Cannot start ticker as accessToken is empty')
    return
  
  global ticker
  ticker = KiteTicker(userConfig['apiKey'], accessToken)
  ticker.on_connect = onConnect
  ticker.on_close = onDisconnect
  ticker.on_error = onError
  ticker.on_reconnect = onReconnect
  ticker.on_noreconnect = onMaxReconnectsAttempt
  ticker.on_ticks = onNewTicks
  ticker.on_order_update = onOrderUpdate

  logging.info('Ticker: Going to connect..')
  ticker.connect(threaded=True)

def registerSymbols(symbols):
  tokens = []
  for symbol in symbols:
    isd = getInstrumentDataBySymbol(symbol)
    token = isd['instrument_token']
    logging.info('registerSymbol: %s token = %s', symbol, token)
    tokens.append(token)

  logging.info('Subscribing tokens %s', tokens)
  ticker.subscribe(tokens)

def stopTicker():
  logging.info('Ticker: stopping..')
  ticker.close(1000, "Manual close")

def onNewTicks(ws, ticks):
  #logging.info('New ticks received %s', ticks)
  for tick in ticks:
    isd = getInstrumentDataByToken(tick['instrument_token'])
    symbol = isd['tradingsymbol']
    logging.info('Tick: %s CMP = %f', symbol, tick['last_price'])

def onConnect(ws, response):
  logging.info('Ticker connection successful.')

def onDisconnect(ws, code, reason):
  logging.error('Ticker got disconnected. code = %d, reason = %s', code, reason)

def onError(ws, code, reason):
  logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

def onReconnect(ws, attemptsCount):
  logging.warn('Ticker reconnecting.. attemptsCount = %d', attemptsCount)

def onMaxReconnectsAttempt(ws):
  logging.error('Ticker max auto reconnects attempted and giving up..')

def onOrderUpdate(ws, data):
  logging.info('Ticker: order update %s', data)




