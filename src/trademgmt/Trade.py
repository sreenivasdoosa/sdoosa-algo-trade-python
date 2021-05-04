import logging
from datetime import datetime

from trademgmt.TradeState import TradeState
from utils.Utils import Utils

class Trade:
  def __init__(self, tradingSymbol):
    self.tradeID = Utils.generateTradeID() # Unique ID for each trade
    self.tradingSymbol = tradingSymbol
    self.strategy = None
    self.direction = None
    self.productType = "MIS"
    self.isFutures = False # Futures trade
    self.isOptions = False # Options trade
    self.optionType = None # CE/PE. Applicable only if isOptions is True
    self.placeMarketOrder = False # True means place the entry order with Market Order Type
    self.noTarget = False # This has to be set to True if target is not applicable for the trade i.e. Square off or SL/Trail SL
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
    self.createTimestamp = datetime.now() # Timestamp when the trade is created (Not triggered)
    self.startTimestamp = None # Timestamp when the trade gets triggered and order placed
    self.endTimestamp = None # Timestamp when the trade ended
    self.profitLoss = 0 # Profit loss of the trade. If trade is Active this shows the unrealized pnl else realized pnl
    self.pnlPercentage = 0 # Profit Loss in percentage terms
    self.exit = 0 # Exit price of the trade
    self.exitReason = None # SL/Target/SquareOff/Any Other
    self.exchange = "NSE" 
    
    self.entryOrder = None # Object of Type ordermgmt.Order
    self.slOrder = None # Object of Type ordermgmt.Order
    self.targetOrder = None # Object of Type ordermgmt.Order

  def printTrade(self):
    logging.info('ID=%s, state=%s, symbol=%s, strategy=%s, direction=%s'
        + ', productType=%s, reqEntry=%f, stopLoss=%f, target=%f'
        + ', entry=%f, exit=%f',
        self.tradeID, self.tradeState, self.tradingSymbol, self.strategy, self.direction,
        self.productType, self.requestedEntry, self.stopLoss, self.target,
        self.entry, self.exit)