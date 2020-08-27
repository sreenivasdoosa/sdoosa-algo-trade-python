import json
import logging
import threading
import time

instrumentsList = None
symbolToInstrumentMap = None
tokenToInstrumentMap = None

def fetchInstruments(kite):
  global instrumentsList
  if instrumentsList:
    return instrumentsList

  logging.info('Going to fetch instruments...')
  instrumentsList = kite.instruments('NSE')
  global symbolToInstrumentMap
  global tokenToInstrumentMap
  symbolToInstrumentMap = {}
  tokenToInstrumentMap = {}
  for isd in instrumentsList:
    tradingSymbol = isd['tradingsymbol']
    instrumentToken = isd['instrument_token']
    # logging.info('%s = %d', tradingSymbol, instrumentToken)
    symbolToInstrumentMap[tradingSymbol] = isd
    tokenToInstrumentMap[instrumentToken] = isd
  
  logging.info('Fetching instruments done. Instruments count = %d', len(instrumentsList))
  return instrumentsList

def getInstrumentDataBySymbol(tradingSymbol):
  return symbolToInstrumentMap[tradingSymbol]

def getInstrumentDataByToken(instrumentToken):
  return tokenToInstrumentMap[instrumentToken]