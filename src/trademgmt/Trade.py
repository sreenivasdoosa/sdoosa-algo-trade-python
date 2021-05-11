import logging

from trademgmt.TradeState import TradeState
from models.ProductType import ProductType

from utils.Utils import Utils

class Trade:
  def __init__(self, tradingSymbol = None):
    self.exchange = "NSE" 
    self.tradeID = Utils.generateTradeID() # Unique ID for each trade
    self.tradingSymbol = tradingSymbol
    self.strategy = ""
    self.direction = ""
    self.productType = ProductType.MIS
    self.isFutures = False # Futures trade
    self.isOptions = False # Options trade
    self.optionType = None # CE/PE. Applicable only if isOptions is True
    self.placeMarketOrder = False # True means place the entry order with Market Order Type
    self.intradaySquareOffTimestamp = None # Can be strategy specific. Some can square off at 15:00:00 some can at 15:15:00 etc.
    self.requestedEntry = 0 # Requested entry
    self.entry = 0 # Actual entry. This will be different from requestedEntry if the order placed is Market order
    self.qty = 0 # Requested quantity
    self.filledQty = 0 # In case partial fill qty is not equal to filled quantity
    self.initialStopLoss = 0 # Initial stop loss
    self.stopLoss = 0 # This is the current stop loss. In case of trailing SL the current stopLoss and initialStopLoss will be different after some time
    self.target = 0 # Target price if applicable
    self.cmp = 0 # Last traded price

    self.tradeState = TradeState.CREATED # state of the trade
    self.timestamp = None # Set this timestamp to strategy timestamp if you are not sure what to set
    self.createTimestamp = Utils.getEpoch() # Timestamp when the trade is created (Not triggered)
    self.startTimestamp = None # Timestamp when the trade gets triggered and order placed
    self.endTimestamp = None # Timestamp when the trade ended
    self.pnl = 0 # Profit loss of the trade. If trade is Active this shows the unrealized pnl else realized pnl
    self.pnlPercentage = 0 # Profit Loss in percentage terms
    self.exit = 0 # Exit price of the trade
    self.exitReason = None # SL/Target/SquareOff/Any Other
    
    self.entryOrder = None # Object of Type ordermgmt.Order
    self.slOrder = None # Object of Type ordermgmt.Order
    self.targetOrder = None # Object of Type ordermgmt.Order

  def equals(self, trade): # compares to trade objects and returns True if equals
    if trade == None:
      return False
    if self.tradeID == trade.tradeID:
      return True
    if self.tradingSymbol != trade.tradingSymbol:
      return False
    if self.strategy != trade.strategy:
      return False  
    if self.direction != trade.direction:
      return False
    if self.productType != trade.productType:
      return False
    if self.requestedEntry != trade.requestedEntry:
      return False
    if self.qty != trade.qty:
      return False
    if self.timestamp != trade.timestamp:
      return False
    return True

  def __str__(self):
    return "ID=" + str(self.tradeID) + ", state=" + self.tradeState + ", symbol=" + self.tradingSymbol \
      + ", strategy=" + self.strategy + ", direction=" + self.direction \
      + ", productType=" + self.productType + ", reqEntry=" + str(self.requestedEntry) \
      + ", stopLoss=" + str(self.stopLoss) + ", target=" + str(self.target) \
      + ", entry=" + str(self.entry) + ", exit=" + str(self.exit) \
      + ", profitLoss" + str(self.pnl)

