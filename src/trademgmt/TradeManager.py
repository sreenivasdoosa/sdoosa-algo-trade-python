import os
import logging
import time
import json
from datetime import datetime

from config.Config import getServerConfig
from core.Controller import Controller
from ticker.ZerodhaTicker import ZerodhaTicker
from trademgmt.Trade import Trade
from trademgmt.TradeState import TradeState
from trademgmt.TradeExitReason import TradeExitReason
from trademgmt.TradeEncoder import TradeEncoder
from ordermgmt.ZerodhaOrderManager import ZerodhaOrderManager
from ordermgmt.OrderInputParams import OrderInputParams
from ordermgmt.Order import Order
from models.OrderType import OrderType
from models.OrderStatus import OrderStatus
from models.Direction import Direction

from utils.Utils import Utils

class TradeManager:
  ticker = None
  trades = [] # to store all the trades
  strategyToInstanceMap = {}
  symbolToCMPMap = {}
  intradayTradesDir = None
  registeredSymbols = []

  @staticmethod
  def run():
    if Utils.isTodayHoliday():
      logging.info("Cannot start TradeManager as Today is Trading Holiday.")
      return

    if Utils.isMarketClosedForTheDay():
      logging.info("Cannot start TradeManager as Market is closed for the day.")
      return

    Utils.waitTillMarketOpens("TradeManager")

    # check and create trades directory for today`s date
    serverConfig = getServerConfig()
    tradesDir = os.path.join(serverConfig['deployDir'], 'trades')
    TradeManager.intradayTradesDir =  os.path.join(tradesDir, Utils.getTodayDateStr())
    if os.path.exists(TradeManager.intradayTradesDir) == False:
      logging.info('TradeManager: Intraday Trades Directory %s does not exist. Hence going to create.', TradeManager.intradayTradesDir)
      os.mkdirs(TradeManager.intradayTradesDir)

    # start ticker service
    brokerName = Controller.getBrokerName()
    if brokerName == "zerodha":
      TradeManager.ticker = ZerodhaTicker()
    #elif brokerName == "fyers" # not implemented
    # ticker = FyersTicker()

    TradeManager.ticker.startTicker()
    TradeManager.ticker.registerListener(TradeManager.tickerListener)

    # sleep for 2 seconds for ticker connection establishment
    time.sleep(2)

    # Load all trades from json files to app memory
    TradeManager.loadAllTradesFromFile()

    # track and update trades in a loop
    while True:
      if Utils.isMarketClosedForTheDay():
        logging.info('TradeManager: Stopping TradeManager as market closed.')
        break

      try:
        # Fetch all order details from broker and update orders in each trade
        TradeManager.fetchAndUpdateAllTradeOrders()
        # track each trade and take necessary action
        TradeManager.trackAndUpdateAllTrades()
      except Exception as e:
        logging.exception("Exception in TradeManager Main thread")

      # save updated data to json file
      TradeManager.saveAllTradesToFile()
      
      # sleep for 30 seconds and then continue
      time.sleep(30)
      logging.info('TradeManager: Main thread woke up..')

  @staticmethod
  def registerStrategy(strategyInstance):
    TradeManager.strategyToInstanceMap[strategyInstance.getName()] = strategyInstance

  @staticmethod
  def loadAllTradesFromFile():
    tradesFilepath = os.path.join(TradeManager.intradayTradesDir, 'trades.json')
    if os.path.exists(tradesFilepath) == False:
      logging.warn('TradeManager: loadAllTradesFromFile() Trades Filepath %s does not exist', tradesFilepath)
      return
    TradeManager.trades = []
    tFile = open(tradesFilepath, 'r')
    tradesData = json.loads(tFile.read())
    for tr in tradesData:
      trade = TradeManager.convertJSONToTrade(tr)
      logging.info('loadAllTradesFromFile trade => %s', trade)
      TradeManager.trades.append(trade)
      if trade.tradingSymbol not in TradeManager.registeredSymbols:
        # Algo register symbols with ticker
        TradeManager.ticker.registerSymbols([trade.tradingSymbol])
        TradeManager.registeredSymbols.append(trade.tradingSymbol)
    logging.info('TradeManager: Successfully loaded %d trades from json file %s', len(TradeManager.trades), tradesFilepath)

  @staticmethod
  def saveAllTradesToFile():
    tradesFilepath = os.path.join(TradeManager.intradayTradesDir, 'trades.json')
    with open(tradesFilepath, 'w') as tFile:
      json.dump(TradeManager.trades, tFile, indent=2, cls=TradeEncoder)
    logging.info('TradeManager: Saved %d trades to file %s', len(TradeManager.trades), tradesFilepath)

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
    if trade.tradingSymbol not in TradeManager.registeredSymbols:
      TradeManager.ticker.registerSymbols([trade.tradingSymbol])
      TradeManager.registeredSymbols.append(trade.tradingSymbol)

  @staticmethod
  def disableTrade(trade, reason):
    if trade != None:
      logging.info('TradeManager: Going to disable trade ID %s with the reason %s', trade.tradeID, reason)
      trade.tradeState = TradeState.DISABLED

  @staticmethod
  def tickerListener(tick):
    # logging.info('tickerLister: new tick received for %s = %f', tick.tradingSymbol, tick.lastTradedPrice);
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
          trade.startTimestamp = Utils.getEpoch()
  
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

    logging.info('TradeManager: Execute trade successful for %s and entryOrder %s', trade, trade.entryOrder)
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
          nowEpoch = Utils.getEpoch()
          if nowEpoch >= trade.intradaySquareOffTimestamp:
            TradeManager.squareOffTrade(trade, TradeExitReason.SQUARE_OFF)
        
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
    oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.LONG 
    oip.productType = trade.productType
    oip.orderType = OrderType.SL_MARKET
    oip.triggerPrice = trade.stopLoss
    oip.qty = trade.qty
    try:
      trade.slOrder = TradeManager.getOrderManager().placeOrder(oip)
    except Exception as e:
      logging.error('TradeManager: Failed to place SL order for tradeID %s: Error => %s', trade.tradeID, str(e))
      return False
    logging.info('TradeManager: Successfully placed SL order %s for tradeID %s', trade.slOrder.orderId, trade.tradeID)
    return True

  @staticmethod
  def placeTargetOrder(trade, isMarketOrder = False):
    oip = OrderInputParams(trade.tradingSymbol)
    oip.direction = Direction.SHORT if trade.direction == Direction.LONG else Direction.LONG
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
    trade.endTimestamp = Utils.getEpoch()
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
      TradeManager.getOrderManager().modifyOrderToMarket(trade.targetOrder)
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

  @staticmethod
  def convertJSONToTrade(jsonData):
    trade = Trade(jsonData['tradingSymbol'])
    trade.tradeID = jsonData['tradeID']
    trade.strategy = jsonData['strategy']
    trade.direction = jsonData['direction']
    trade.productType = jsonData['productType']
    trade.isFutures = jsonData['isFutures']
    trade.isOptions = jsonData['isOptions']
    trade.optionType = jsonData['optionType']
    trade.placeMarketOrder = jsonData['placeMarketOrder']
    trade.intradaySquareOffTimestamp = jsonData['intradaySquareOffTimestamp']
    trade.requestedEntry = jsonData['requestedEntry']
    trade.entry = jsonData['entry']
    trade.qty = jsonData['qty']
    trade.filledQty = jsonData['filledQty']
    trade.initialStopLoss = jsonData['initialStopLoss']
    trade.stopLoss = jsonData['stopLoss']
    trade.target = jsonData['target']
    trade.cmp = jsonData['cmp']
    trade.tradeState = jsonData['tradeState']
    trade.timestamp = jsonData['timestamp']
    trade.createTimestamp = jsonData['createTimestamp']
    trade.startTimestamp = jsonData['startTimestamp']
    trade.endTimestamp = jsonData['endTimestamp']
    trade.pnl = jsonData['pnl']
    trade.pnlPercentage = jsonData['pnlPercentage']
    trade.exit = jsonData['exit']
    trade.exitReason = jsonData['exitReason']
    trade.exchange = jsonData['exchange']
    trade.entryOrder = TradeManager.convertJSONToOrder(jsonData['entryOrder'])
    trade.slOrder = TradeManager.convertJSONToOrder(jsonData['slOrder'])
    trade.targetOrder = TradeManager.convertJSONToOrder(jsonData['targetOrder'])
    return trade

  @staticmethod
  def convertJSONToOrder(jsonData):
    if jsonData == None:
      return None
    order = Order()
    order.tradingSymbol = jsonData['tradingSymbol']
    order.exchange = jsonData['exchange']
    order.productType = jsonData['productType']
    order.orderType = jsonData['orderType']
    order.price = jsonData['price']
    order.triggerPrice = jsonData['triggerPrice']
    order.qty = jsonData['qty']
    order.orderId = jsonData['orderId']
    order.orderStatus = jsonData['orderStatus']
    order.averagePrice = jsonData['averagePrice']
    order.filledQty = jsonData['filledQty']
    order.pendingQty = jsonData['pendingQty']
    order.orderPlaceTimestamp = jsonData['orderPlaceTimestamp']
    order.lastOrderUpdateTimestamp = jsonData['lastOrderUpdateTimestamp']
    order.message = jsonData['message']
    return order

