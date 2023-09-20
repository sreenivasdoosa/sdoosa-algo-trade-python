import os
import logging
import time
import json
import csv
import threading
from datetime import datetime

from config.Config import getServerConfig
from core.Controller import Controller
from core.Quotes import Quotes
from ticker.ZerodhaTicker import ZerodhaTicker
from ticker.AngelOneTicker import AngelOneTicker
from instruments.Instruments import Instruments
from utils.Utils import Utils

class DataManager:
  ticker = None
  symbolToFileMap = {}
  symbolToDataListMap = {}
  dataDir = None
  registeredSymbols = []
  dataColumns = ['date','open','high','low','close','volume','oi']
  #brokerLogin = Controller.getBrokerLogin()
  #brokerAppDetails = brokerLogin.getBrokerAppDetails()
  #brokerHandle = brokerLogin.getBrokerHandle()

  @staticmethod
  def run(sleepSeconds):
    if Utils.isTodayHoliday():
      logging.info("Cannot start DataManager as Today is Trading Holiday.")
      return

    if Utils.isMarketClosedForTheDay():
      logging.info("Cannot start DataManager as Market is closed for the day.")
      return

    Utils.waitTillMarketOpens("DataManager")

    time.sleep(sleepSeconds)

    # check and create trades directory for today`s date
    serverConfig = getServerConfig()
    DataManager.dataDir = os.path.join(serverConfig['deployDir'], 'data')
    if not os.path.exists(DataManager.dataDir):
      os.mkdir(DataManager.dataDir)

    #DataManager.loadAllSymbolsFromFiles()

    #schedule.every(5).minutes.do(job)

    #while 1:
    #  schedule.run_pending()
    #  time.sleep(1)

    # start ticker service
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      DataManager.ticker = ZerodhaTicker("DataManager")
    elif brokerName == "angel":
      DataManager.ticker = AngelOneTicker("DataManager")

    threading.Thread(target=DataManager.storeDataEvery5Minutes).start()

    DataManager.ticker.registerListener(DataManager.tickerListener)
    DataManager.ticker.registerConnectionListener(DataManager.loadAllSymbolsFromFiles)
    DataManager.ticker.startTicker()

  @staticmethod
  def loadAllSymbolsFromFiles():
    dataFilepath = DataManager.dataDir
    if os.path.exists(dataFilepath) == False:
      logging.warn('DataManager: loadAllSymbolsFromFiles() Data Filepath %s does not exist', dataFilepath)
      return

    symbolsFromFiles = [os.path.splitext(filename)[0] for filename in os.listdir(dataFilepath)]
    listSym = list(set(symbolsFromFiles).symmetric_difference(DataManager.registeredSymbols))
    logging.info('listSym %s', listSym)
    for symbol in listSym:
        DataManager.ticker.registerSymbols([symbol])
        DataManager.registeredSymbols.append(symbol)
    logging.info('DataManager: Successfully loaded %d symbols from data dir %s', len(DataManager.registeredSymbols), dataFilepath)

  @staticmethod
  def addNewSymbol(symbol):
    logging.info('DataManager: addNewSymbol called for %s', symbol)
    if symbol == None:
      return
    if symbol in DataManager.registeredSymbols:
      logging.warn('DataManager: Symbol already exists so not adding again. %s', symbol)
      return

    symbolDataFile = os.path.join(DataManager.dataDir, symbol+'.csv')
    with open(symbolDataFile, 'w', newline='') as file:
      writer = csv.writer(file)
    DataManager.symbolToFileMap[symbol] = symbolDataFile
    DataManager.symbolToDataListMap[symbol] = [DataManager.dataColumns]

    # Register the symbol with ticker so that we will start getting ticks for this symbol
    DataManager.ticker.registerSymbols([symbol])
    DataManager.registeredSymbols.append(symbol)

    logging.info('DataManager: registeredSymbols %s', DataManager.registeredSymbols)

    
  @staticmethod
  def tickerListener(tick):
    logging.info('DataManager: tickerListener for Tick = %s',tick.tradingSymbol)
    #write tick data to respective ticker file at an interval defined in the config
    if tick.tradingSymbol in DataManager.registeredSymbols:
      DataManager.symbolToDataListMap[tick.tradingSymbol].append([tick.timestamp,tick.open,tick.high,tick.low,tick.close,tick.volume,tick.oi])
 
  def storeDataEvery5Minutes():
    nowEpoch = Utils.getEpoch()
    marketStartTimeEpoch = Utils.getEpoch(Utils.getMarketStartTime())
    waitSeconds = 5*60
    while waitSeconds > 0:
      logging.info("DataManager: Waiting for %d seconds ...", waitSeconds)
      time.sleep(waitSeconds)
      DataManager.storeDataToFiles()
      logging.info("DataManager: Stored data to files")

  def getData(symbol):
    Quotes.getQuote(symbol)
    
  def storeDataToFiles():
    for symbol in DataManager.registeredSymbols:
      with open(DataManager.symbolToFileMap[symbol], 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(DataManager.symbolToDataListMap[symbol])
        DataManager.symbolToDataListMap[symbol] = []