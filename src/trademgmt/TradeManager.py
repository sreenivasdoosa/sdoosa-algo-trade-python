import logging
import time

from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from utils.Utils import Utils

class TradeManager:
  @staticmethod
  def init():
    if Utils.isTodayHoliday():
      logging.info("Cannot start TradeManager as Today is Trading Holiday.")
      return

    if Utils.isMarketClosedForTheDay():
      logging.info("Cannot start TradeManager as Market is closed for the day.")
      return

    Utils.waitTillMarketOpens("TradeManager")

    # start ticker service
    ticker = None
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      ticker = ZerodhaTicker()
    #elif brokerName == "fyers" # not implemented
    # ticker = FyersTicker()

    ticker.startTicker()
    ticker.registerListener(TradeManager.tickerListener)

    # Currenlty just having a sleep here to wait for ticker connection successful
    # TODO: Proper Implementation: Add onConnect() callback and register symbols afterwards
    #time.sleep(2)
    #ticker.registerSymbols(['SBIN', 'RELIANCE'])

  @staticmethod
  def tickerListener(tick):
    logging.info('tickerLister: onNewTick %s', vars(tick));

