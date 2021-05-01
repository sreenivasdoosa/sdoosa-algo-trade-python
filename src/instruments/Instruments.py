import logging

from core.Controller import Controller

class Instruments:
  instrumentsList = None
  symbolToInstrumentMap = None
  tokenToInstrumentMap = None  

  @staticmethod
  def fetchInstruments():
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    if Instruments.instrumentsList:
      return Instruments.instrumentsList

    logging.info('Going to fetch instruments...')
    instrumentsList = brokerHandle.instruments('NSE')
    Instruments.symbolToInstrumentMap = {}
    Instruments.tokenToInstrumentMap = {}
    for isd in instrumentsList:
      tradingSymbol = isd['tradingsymbol']
      instrumentToken = isd['instrument_token']
      # logging.info('%s = %d', tradingSymbol, instrumentToken)
      Instruments.symbolToInstrumentMap[tradingSymbol] = isd
      Instruments.tokenToInstrumentMap[instrumentToken] = isd
    
    logging.info('Fetching instruments done. Instruments count = %d', len(instrumentsList))
    Instruments.instrumentsList = instrumentsList # assign the list to static variable
    return instrumentsList

  @staticmethod
  def getInstrumentDataBySymbol(tradingSymbol):
    return Instruments.symbolToInstrumentMap[tradingSymbol]

  @staticmethod
  def getInstrumentDataByToken(instrumentToken):
    return Instruments.tokenToInstrumentMap[instrumentToken]
    