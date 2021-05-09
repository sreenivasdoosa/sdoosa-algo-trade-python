import logging
import time
from datetime import datetime

from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from trademgmt.TradeState import TradeState
from trademgmt.TradeExitReason import TradeExitReason
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.OrderInputParams import OrderInputParams
from models.OrderType import OrderType
from models.OrderStatus import OrderStatus
from models.Direction import Direction

from utils.Utils import Utils

class TradeManager:
  ticker = None
  trades = [] # to store all the trades
  strategyToInstanceMap = {}
  symbolToCMPMap = {}

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
    TradeManager.symbolToCMPMap[tick.tradingSymbol] = tick.lastTradedPrice # Store the latest tick in map
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
          trade.startTimestamp = datetime.now()
  
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
    trade.initialStopLoss = trade.stopLoss
    # Create order input params object and place order
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
    for trade in TradeManager.trades:
      if trade.tradeState == TradeState.ACTIVE:
        if trade.intradaySquareOffTimestamp != None:
          now = datetime.now()
          if now >= trade.intradaySquareOffTimestamp:
            TradeManager.squareOffTrade(trade, TradeExitReason.SQUARE_OFF)
        else:
          TradeManager.trackEntryOrder(trade)
          TradeManager.trackSLOrder(trade)
          TradeManager.trackTargetOrder(trade)

  @staticmethod
  def trackEntryOrder(trade):
    if trade.tradeState != TradeState.ACTIVE:
      return

    if trade.entryOrder == None:
      return

    if trade.entryOrder.orderStatus == OrderStatus.CANCELLED or trade.entryOrder.orderStatus == OrderStatus.REJECTED:
      trade.tradeState = TradeState.CANCELLED

    trade.filledQty = trade.entryOrder.filledQty
    if trade.filledQty > 0:
      trade.entry = trade.entryOrder.averagePrice
    # Update the current market price and calculate pnl
    trade.cmp = TradeManager.symbolToCMPMap[trade.tradingSymbol]
    Utils.calculateTradePnl(trade)

  @staticmethod
  def trackSLOrder(trade):
    if trade.tradeState != TradeState.ACTIVE:
      return
    if trade.stopLoss == 0: # Do not place SL order if no stoploss provided
      return
    if trade.slOrder == None:
      # Place SL order
      TradeManager.placeSLOrder(trade)
    else:
      if trade.slOrder.orderStatus == OrderStatus.COMPLETE:
        # SL Hit
        exit = trade.slOrder.averagePrice
        TradeManager.setTradeToCompleted(trade, exit, TradeExitReason.SL_HIT)
        # Make sure to cancel target order if exists
        TradeManager.cancelTargetOrder(trade)

      elif trade.slOrder.orderStatus == OrderStatus.CANCELLED:
        # SL order cancelled outside of algo (manually or by broker or by exchange)
        logging.error('SL order %s for tradeID %s cancelled outside of Algo. Setting the trade as completed with exit price as current market price.', trade.slOrder.orderId, trade.tradeID)
        exit = TradeManager.symbolToCMPMap[trade.tradingSymbol]
        TradeManager.setTradeToCompleted(trade, exit, TradeExitReason.SL_CANCELLED)
        # Cancel target order if exists
        TradeManager.cancelTargetOrder(trade)

  @staticmethod
  def trackTargetOrder(trade):
    if trade.tradeState != TradeState.ACTIVE:
      return
    if trade.target == 0: # Do not place Target order if no target provided
      return
    if trade.targetOrder == None:
      # Place Target order
      TradeManager.placeTargetOrder(trade)
    else:
      if trade.targetOrder.orderStatus == OrderStatus.COMPLETE:
        # Target Hit
        exit = trade.targetOrder.averagePrice
        TradeManager.setTradeToCompleted(trade, exit, TradeExitReason.TARGET_HIT)
        # Make sure to cancel sl order
        TradeManager.cancelSLOrder(trade)

      elif trade.targetOrder.orderStatus == OrderStatus.CANCELLED:
        # Target order cancelled outside of algo (manually or by broker or by exchange)
        logging.error('Target order %s for tradeID %s cancelled outside of Algo. Setting the trade as completed with exit price as current market price.', trade.targetOrder.orderId, trade.tradeID)
        exit = TradeManager.symbolToCMPMap[trade.tradingSymbol]
        TradeManager.setTradeToCompleted(trade, exit, TradeExitReason.TARGET_CANCELLED)
        # Cancel SL order
        TradeManager.cancelSLOrder(trade)

  @staticmethod
  def placeSLOrder(trade):
    oip = OrderInputParams(trade.tradingSymbol)
    oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.SHORT 
    oip.productType = trade.productType
    oip.orderType = OrderType.SL_MARKET
    oip.triggerPrice = trade.stopLoss
    oip.qty = trade.qty
    try:
      trade.slOrder = TradeManager.getOrderManager().placeOrder(oip)
    except Exception as e:
      logging.exrror('TradeManager: Failed to place SL order for tradeID %s: Error => %s', trade.tradeID, str(e))
      return False
    logging.info('TradeManager: Successfully placed SL order %s for tradeID %s', trade.slOrder.orderId, trade.tradeID)
    return True

  @staticmethod
  def placeTargetOrder(trade, isMarketOrder = False):
    oip = OrderInputParams(trade.tradingSymbol)
    oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.SHORT 
    oip.productType = trade.productType
    oip.orderType = OrderType.MARKET if isMarketOrder == True else OrderType.LIMIT
    oip.price = 0 if isMarketOrder == True else trade.target
    oip.qty = trade.qty
    try:
      trade.targetOrder = TradeManager.getOrderManager().placeOrder(oip)
    except Exception as e:
      logging.exrror('TradeManager: Failed to place Target order for tradeID %s: Error => %s', trade.tradeID, str(e))
      return False
    logging.info('TradeManager: Successfully placed Target order %s for tradeID %s', trade.targetOrder.orderId, trade.tradeID)
    return True

  @staticmethod
  def cancelEntryOrder(trade):
    if trade.entryOrder == None:
      return
    if trade.entryOrder.orderStatus == OrderStatus.CANCELLED:
      return
    try:
      TradeManager.getOrderManager().cancelOrder(trade.entryOrder)
    except Exception as e:
      logging.exrror('TradeManager: Failed to cancel Entry order %s for tradeID %s: Error => %s', trade.entryOrder.orderId, trade.tradeID, str(e))
    logging.info('TradeManager: Successfully cancelled Entry order %s for tradeID %s', trade.entryOrder.orderId, trade.tradeID)

  @staticmethod
  def cancelSLOrder(trade):
    if trade.slOrder == None:
      return
    if trade.slOrder.orderStatus == OrderStatus.CANCELLED:
      return
    try:
      TradeManager.getOrderManager().cancelOrder(trade.slOrder)
    except Exception as e:
      logging.exrror('TradeManager: Failed to cancel SL order %s for tradeID %s: Error => %s', trade.slOrder.orderId, trade.tradeID, str(e))
    logging.info('TradeManager: Successfully cancelled SL order %s for tradeID %s', trade.slOrder.orderId, trade.tradeID)

  @staticmethod
  def cancelTargetOrder(trade):
    if trade.targetOrder == None:
      return
    if trade.targetOrder.orderStatus == OrderStatus.CANCELLED:
      return
    try:
      TradeManager.getOrderManager().cancelOrder(trade.targetOrder)
    except Exception as e:
      logging.exrror('TradeManager: Failed to cancel Target order %s for tradeID %s: Error => %s', trade.targetOrder.orderId, trade.tradeID, str(e))
    logging.info('TradeManager: Successfully cancelled Target order %s for tradeID %s', trade.targetOrder.orderId, trade.tradeID)

  @staticmethod
  def setTradeToCompleted(trade, exit, exitReason = None):
    trade.tradeState = TradeState.COMPLETED
    trade.exit = exit
    trade.exitReason = exitReason if trade.exitReason == None else trade.exitReason
    trade = Utils.calculateTradePnl(trade)
    logging.info('TradeManager: setTradeToCompleted strategy = %s, symbol = %s, qty = %d, entry = %f, exit = %f, pnl = %f, exit reason = %s', trade.strategy, trade.tradingSymbol, trade.filledQty, trade.entry, trade.exit, trade.pnl, trade.exitReason)

  @staticmethod
  def squareOffTrade(trade, reason = TradeExitReason.SQUARE_OFF):
    logging.info('TradeManager: squareOffTrade called for tradeID %s with reason %s', trade.tradeID, reason)
    if trade == None or trade.tradeState != TradeState.ACTIVE:
      return

    trade.exitReason = reason
    if trade.entryOrder != None:
      if trade.entryOrder.orderStatus == OrderStatus.OPEN:
        # Cancel entry order if it is still open (not filled or partially filled case)
        TradeManager.cancelEntryOrder(trade)

    if trade.slOrder != None:
      TradeManager.cancelSLOrder(trade)

    if trade.targetOrder != None:
      # Change target order type to MARKET to exit position immediately
      logging.info('TradeManager: changing target order %s to MARKET to exit position for tradeID %s', trade.targetOrder.orderId, trade.tradeID)
      TradeManager.getOrderManager.modifyOrderToMarket(trade.targetOrder)
    else:
      # Place new target order to exit position
      logging.info('TradeManager: placing new target order to exit position for tradeID %s', trade.tradeID)
      TradeManager.placeTargetOrder(trade, true)

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
