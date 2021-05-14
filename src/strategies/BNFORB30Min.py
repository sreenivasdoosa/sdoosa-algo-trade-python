import logging
from datetime import datetime

from instruments.Instruments import Instruments
from models.Direction import Direction
from models.ProductType import ProductType
from strategies.BaseStrategy import BaseStrategy
from utils.Utils import Utils
from trademgmt.Trade import Trade
from trademgmt.TradeManager import TradeManager

# Each strategy has to be derived from BaseStrategy
class BNFORB30Min(BaseStrategy):
  __instance = None

  @staticmethod
  def getInstance(): # singleton class
    if BNFORB30Min.__instance == None:
      BNFORB30Min()
    return BNFORB30Min.__instance

  def __init__(self):
    if BNFORB30Min.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      BNFORB30Min.__instance = self
    # Call Base class constructor
    super().__init__("BNFORB30Min")
    # Initialize all the properties specific to this strategy
    self.productType = ProductType.MIS
    self.symbols = []
    self.slPercentage = 0
    self.targetPerncetage = 0
    self.startTimestamp = Utils.getTimeOfToDay(9, 45, 0) # When to start the strategy. Default is Market start time
    self.stopTimestamp = Utils.getTimeOfToDay(14, 30, 0) # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
    self.squareOffTimestamp = Utils.getTimeOfToDay(15, 0, 0) # Square off time
    self.capital = 100000 # Capital to trade (This is the margin you allocate from your broker account for this strategy)
    self.leverage = 0
    self.maxTradesPerDay = 1 # Max number of trades per day under this strategy
    self.isFnO = True # Does this strategy trade in FnO or not
    self.capitalPerSet = 100000 # Applicable if isFnO is True (1 set means 1CE/1PE or 2CE/2PE etc based on your strategy logic)

  def process(self):
    now = datetime.now()
    processEndTime = Utils.getTimeOfToDay(9, 50, 0)
    if now < self.startTimestamp:
      return
    if now > processEndTime:
      # We are interested in creating the symbol only between 09:45 and 09:50 
      # since we are not using historical candles so not aware of exact high and low of the first 30 mins
      return

    symbol = Utils.prepareMonthlyExpiryFuturesSymbol('BANKNIFTY')
    quote = self.getQuote(symbol)
    if quote == None:
        logging.error('%s: Could not get quote for %s', self.getName(), symbol)
        return
    
    if symbol not in self.tradesCreatedSymbols:
      self.generateTrade(symbol, Direction.LONG, quote.high, quote.low)
      self.generateTrade(symbol, Direction.SHORT, quote.high, quote.low)
      # add symbol to created list
      self.tradesCreatedSymbols.append(symbol)

  def generateTrade(self, tradingSymbol, direction, high, low):
    trade = Trade(tradingSymbol)
    trade.strategy = self.getName()
    trade.isFutures = True
    trade.direction = direction
    trade.productType = self.productType
    trade.placeMarketOrder = True
    trade.requestedEntry = high if direction == Direction.LONG else low
    trade.timestamp = Utils.getEpoch(self.startTimestamp) # setting this to strategy timestamp
    # Calculate lots
    numLots = self.calculateLotsPerTrade()
    isd = Instruments.getInstrumentDataBySymbol(tradingSymbol) # Get instrument data to know qty per lot
    trade.qty = isd['lot_size']
    
    trade.stopLoss = low if direction == Direction.LONG else high
    slDiff = high - low
    # target is 1.5 times of SL
    if direction == 'LONG':
      trade.target = Utils.roundToNSEPrice(trade.requestedEntry + 1.5 * slDiff)
    else:
      trade.target = Utils.roundToNSEPrice(trade.requestedEntry - 1.5 * slDiff)

    trade.intradaySquareOffTimestamp = Utils.getEpoch(self.squareOffTimestamp)
    # Hand over the trade to TradeManager
    TradeManager.addNewTrade(trade)

  def shouldPlaceTrade(self, trade, tick):
    # First call base class implementation and if it returns True then only proceed
    if super().shouldPlaceTrade(trade, tick) == False:
      return False

    if tick == None:
      return False

    if trade.direction == Direction.LONG and tick.lastTradedPrice > trade.requestedEntry:
      return True
    elif trade.direction == Direction.SHORT and tick.lastTradedPrice < trade.requestedEntry:
      return True
    return False
