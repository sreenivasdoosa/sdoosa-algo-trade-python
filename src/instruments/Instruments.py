import os
import logging
import json

from config.Config import getServerConfig, getTimestampsData, saveTimestampsData
from core.Controller import Controller
from utils.Utils import Utils

class Instruments:
  instrumentsList = None
  symbolToInstrumentMap = None
  tokenToInstrumentMap = None

  @staticmethod
  def shouldFetchFromServer():
    timestamps = getTimestampsData()
    if 'instrumentsLastSavedAt' not in timestamps:
      return True
    lastSavedTimestamp = timestamps['instrumentsLastSavedAt']
    nowEpoch = Utils.getEpoch()
    if nowEpoch - lastSavedTimestamp >= 24 * 60* 60:
      logging.info("Instruments: shouldFetchFromServer() returning True as its been 24 hours since last fetch.")
      return True
    return False

  @staticmethod
  def updateLastSavedTimestamp():
    timestamps = getTimestampsData()
    timestamps['instrumentsLastSavedAt'] = Utils.getEpoch()
    saveTimestampsData(timestamps)

  @staticmethod
  def loadInstruments():
    serverConfig = getServerConfig()
    instrumentsFilepath = os.path.join(serverConfig['deployDir'], 'instruments.json')
    if os.path.exists(instrumentsFilepath) == False:
      logging.warn('Instruments: instrumentsFilepath %s does not exist', instrumentsFilepath)
      return [] # returns empty list

    isdFile = open(instrumentsFilepath, 'r')
    instruments = json.loads(isdFile.read())
    logging.info('Instruments: loaded %d instruments from file %s', len(instruments), instrumentsFilepath)
    return instruments

  @staticmethod
  def saveInstruments(instruments = []):
    serverConfig = getServerConfig()
    instrumentsFilepath = os.path.join(serverConfig['deployDir'], 'instruments.json')
    with open(instrumentsFilepath, 'w') as isdFile:
      json.dump(instruments, isdFile, indent=2, default=str)
    logging.info('Instruments: Saved %d instruments to file %s', len(instruments), instrumentsFilepath)
    # Update last save timestamp
    Instruments.updateLastSavedTimestamp()

  @staticmethod
  def fetchInstrumentsFromServer():
    instrumentsList = []
    try:
      brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
      logging.info('Going to fetch instruments from server...')
      instrumentsList = brokerHandle.instruments('NSE')
      instrumentsListFnO = brokerHandle.instruments('NFO')
      # Add FnO instrument list to the main list
      instrumentsList.extend(instrumentsListFnO)
      logging.info('Fetched %d instruments from server.', len(instrumentsList))
    except Exception as e:
      logging.exception("Exception while fetching instruments from server")
    return instrumentsList

  @staticmethod
  def fetchInstruments():
    if Instruments.instrumentsList:
      return Instruments.instrumentsList

    instrumentsList = Instruments.loadInstruments()
    if len(instrumentsList) == 0 or Instruments.shouldFetchFromServer() == True:
      instrumentsList = Instruments.fetchInstrumentsFromServer()
      # Save instruments to file locally
      if len(instrumentsList) > 0:
        Instruments.saveInstruments(instrumentsList)

    if len(instrumentsList) == 0:
      print("Could not fetch/load instruments data. Hence exiting the app.")
      logging.error("Could not fetch/load instruments data. Hence exiting the app.");
      exit(-2)
    
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
    