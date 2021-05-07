import logging
import time

from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from trademgmt.TradeState import TradeState
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.OrderInputParams import OrderInputParams
from models.OrderType import OrderType

from utils.Utils import Utils

class TradeManager:
  ticker = None
  trades = [] # to store all the trades
  strategyToInstanceMap = {}

  @staticmethod
  def run():
    if Utils.isTodayHoliday():
      logging.info("Cannot start TradeManager as Today is Trading Holiday.")
      return

    if Utils.isMarketClosedForTheDay():
      logging.info("Cannot start TradeManager as Market is closed for the day.")
      return

    Utils.waitTillMarketOpens("TradeManager")

    # start ticker service
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      TradeManager.ticker = ZerodhaTicker()
    #elif brokerName == "fyers" # not implemented
    # ticker = FyersTicker()

    TradeManager.ticker.startTicker()
    TradeManager.ticker.registerListener(TradeManager.tickerListener)

    # track and update trades in a loop
    while True:
      if Utils.isMarketClosedForTheDay():
        logging.info('TradeManager: Stopping TradeManager as market closed.')
        break

      # Fetch all order details from broker and update orders in each trade
      TradeManager.fetchAndUpdateAllTradeOrders()

      # track each trade and take necessary action
      TradeManager.trackAndUpdateAllTrades()

      time.sleep(60 * 1000) # sleep for 60 seconds

  @staticmethod
  def registerStrategy(strategyInstance):
    TradeManager.strategyToInstanceMap[strategyInstance.getName()] = strategyInstance

  @staticmethod
  def addNewTrade(trade):
    if trade == None:
      return
    logging.info('TradeManager: addNewTrade called for %s', trade)
    for tr in TradeManager.trades:
      if tr.equals(trade):
        logging.warn('TradeManager: Trade already exists so not adding again. %s', trade)
        return
    # Add the new trade to the list
    TradeManager.trades.append(trade)
    logging.info('TradeManager: trade %s added successfully to the list', trade.tradeID)
    # Register the symbol with ticker so that we will start getting ticks for this symbol
    TradeManager.ticker.registerSymbols([trade.tradingSymbol])

  @staticmethod
  def disableTrade(trade, reason):
    if trade != None:
      logging.info('TradeManager: Going to disable trade ID %s with the reason %s', trade.tradeID, reason)
      trade.tradeState = TradeState.DISABLED

  @staticmethod
  def tickerListener(tick):
    logging.info('tickerLister: new tick received for %s = %f', tick.tradingSymbol, tick.lastTradedPrice);
    # On each new tick, get a created trade and call its strategy whether to place trade or not
    for strategy in TradeManager.strategyToInstanceMap:
      trade = TradeManager.getUntriggeredTrade(tick.tradingSymbol, strategy)
      if trade == None:
        continue
      strategyInstance = TradeManager.strategyToInstanceMap[strategy]
      if strategyInstance.shouldPlaceTrade(trade, tick):
        # place the trade
        isSuccess = TradeManager.executeTrade(trade)
        if isSuccess == True:
          # set trade state to ACTIVE
          trade.tradeState = TradeState.ACTIVE
  
  @staticmethod
  def getUntriggeredTrade(tradingSymbol, strategy):
    trade = None
    for tr in TradeManager.trades:
      if tr.tradeState == TradeState.DISABLED:
        continue
      if tr.tradeState != TradeState.CREATED:
        continue
      if tr.tradingSymbol != tradingSymbol:
        continue
      if tr.strategy != strategy:
        continue
      trade = tr
      break
    return trade

  @staticmethod
  def executeTrade(trade):
    logging.info('TradeManager: Execute trade called for %s', trade)
    oip = OrderInputParams(trade.tradingSymbol)
    oip.direction = trade.direction
    oip.productType = trade.productType
    oip.orderType = OrderType.MARKET if trade.placeMarketOrder == True else OrderType.LIMIT
    oip.price = trade.requestedEntry
    oip.qty = trade.qty
    try:
      trade.entryOrder = TradeManager.getOrderManager().placeOrder(oip)
    except Exception as e:
      logging.exrror('TradeManager: Execute trade failed for tradeID %s: Error => %s', trade.tradeID, str(e))
      return False

    logging.info('TradeManager: Execute trade successful for %s', trade)
    return True

  @staticmethod
  def fetchAndUpdateAllTradeOrders():
    allOrders = []
    for trade in TradeManager.trades:
      if trade.entryOrder != None:
        allOrders.append(trade.entryOrder)
      if trade.slOrder != None:
        allOrders.append(trade.slOrder)
      if trade.targetOrder != None:
        allOrders.append(trade.targetOrder)

    TradeManager.getOrderManager().fetchAndUpdateAllOrderDetails(allOrders)

  @staticmethod
  def trackAndUpdateAllTrades():
    logging.info('trackAndUpdateAllTrades: To be implemented')

  @staticmethod
  def getOrderManager():
    orderManager = None
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      orderManager = ZerodhaOrderManager()
    #elif brokerName == "fyers": # Not implemented
    return orderManager

  @staticmethod
  def getNumberOfTradesPlacedByStrategy(strategy):
    count = 0
    for trade in TradeManager.trades:
      if trade.strategy != strategy:
        continue
      if trade.tradeState == TradeState.CREATED or trade.tradeState == TradeState.DISABLED:
        continue
      # consider active/completed/cancelled trades as trades placed
      count += 1
    return count
