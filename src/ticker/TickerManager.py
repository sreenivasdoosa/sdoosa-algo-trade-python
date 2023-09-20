import os
import logging
import time
import json
import threading
from datetime import datetime

from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from ticker.AngelOneTicker import AngelOneTicker
from utils.Utils import Utils

class TickerManager:
  ticker = None
  registeredTickListeners = []
  registeredConnectionListeners = []
  @staticmethod
  def run(sleepSeconds,context):
    if Utils.isTodayHoliday():
      logging.info("Cannot start TickerManager as Today is Trading Holiday.")
      return

    if Utils.isMarketClosedForTheDay():
      logging.info("Cannot start TickerManager as Market is closed for the day.")
      return

    Utils.waitTillMarketOpens(context)

    time.sleep(sleepSeconds)

    # start ticker service
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      TickManager.ticker = ZerodhaTicker(context)
    elif brokerName == "angel":
      TickManager.ticker = AngelOneTicker(context)

  @staticmethod
  def startTicker():
    TickerManager.ticker.startTicker()

  @staticmethod
  def addTickListener(listener):
    logging.info('TickerManager: addTickListener called for %s', listener)
    if listener == None:
      return
    if listener in TickManager.registeredTickListeners:
      logging.warn('TickerManager: listener already exists so not adding again. %s', listener)
      return

    # Register the listener
    TickerManager.ticker.registerListener(listener)
    TickerManager.registeredTickListeners.append(listener)

    logging.info('TickerManager: registeredTickListeners %s', TickerManager.registeredTickListeners)

  @staticmethod
  def addConnectionListener(listener):
    logging.info('TickerManager: addConnectionListener called for %s', listener)
    if listener == None:
      return
    if listener in TickManager.registeredConnectionListeners:
      logging.warn('TickerManager: listener already exists so not adding again. %s', listener)
      return

    # Register the listener
    TickerManager.ticker.registerConnectionListener(listener)
    TickerManager.registeredConnectionListeners.append(listener)

    logging.info('TickerManager: addConnectionListener %s', TickerManager.addConnectionListener)
