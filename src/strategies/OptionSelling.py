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
class OptionSelling(BaseStrategy):
  __instance = None

  @staticmethod
  def getInstance(): # singleton class
    if OptionSelling.__instance == None:
      OptionSelling()
    return OptionSelling.__instance

  def __init__(self):
    if OptionSelling.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      OptionSelling.__instance = self
    # Call Base class constructor
    super().__init__("OptionSelling")
    # Initialize all the properties specific to this strategy
    self.productType = ProductType.MIS
    self.symbols = []
    self.slPercentage = 50
    self.targetPercentage = 0
    self.startTimestamp = Utils.getTimeOfToDay(9, 30, 0) # When to start the strategy. Default is Market start time
    self.stopTimestamp = Utils.getTimeOfToDay(14, 30, 0) # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
    self.squareOffTimestamp = Utils.getTimeOfToDay(15, 15, 0) # Square off time
    self.capital = 100000 # Capital to trade (This is the margin you allocate from your broker account for this strategy)
    self.leverage = 0
    self.maxTradesPerDay = 2 # (1 CE + 1 PE) Max number of trades per day under this strategy
    self.isFnO = True # Does this strategy trade in FnO or not
    self.capitalPerSet = 100000 # Applicable if isFnO is True (1 set means 1CE/1PE or 2CE/2PE etc based on your strategy logic)

  def canTradeToday(self):
    if Utils.isTodayOneDayBeforeWeeklyExpiryDay() == True:
      logging.info('%s: Today is one day before weekly expiry date hence going to trade this strategy', self.getName())
      return True
    if Utils.isTodayWeeklyExpiryDay() == True:
      logging.info('%s: Today is weekly expiry day hence going to trade this strategy today', self.getName())
      return True
    logging.info('%s: Today is neither day before expiry nor expiry day. Hence NOT going to trade this strategy today', self.getName())
    return False

  def process(self):
    now = datetime.now()
    if now < self.startTimestamp:
      return
    if len(self.tradesCreatedSymbols) >= 2:
      return

    # Get current market price of Nifty Future
    futureSymbol = Utils.prepareMonthlyExpiryFuturesSymbol('NIFTY')
    quote = self.getQuote(futureSymbol)
    if quote == None:
      logging.error('%s: Could not get quote for %s', self.getName(), futureSymbol)
      return

    ATMStrike = Utils.getNearestStrikePrice(quote.lastTradedPrice, 50)
    logging.info('%s: Nifty CMP = %f, ATMStrike = %d', self.getName(), quote.lastTradedPrice, ATMStrike)

    ATMPlus50CESymbol = Utils.prepareWeeklyOptionsSymbol("NIFTY", ATMStrike + 50, 'CE')
    ATMMinus50PESymbol = Utils.prepareWeeklyOptionsSymbol("NIFTY", ATMStrike - 50, 'PE')
    logging.info('%s: ATMPlus50CE = %s, ATMMinus50PE = %s', self.getName(), ATMPlus50CESymbol, ATMMinus50PESymbol)

    if len(self.tradesCreatedSymbols) == 0:
      self.generateTrades(ATMPlus50CESymbol, ATMMinus50PESymbol)

  def generateTrades(self, ATMPlus50CESymbol, ATMMinus50PESymbol):
    numLots = self.calculateLotsPerTrade()
    quoteATMPlus50CESymbol = self.getQuote(ATMPlus50CESymbol)
    quoteATMMinus50PESymbol = self.getQuote(ATMMinus50PESymbol)
    if quoteATMPlus50CESymbol == None or quoteATMMinus50PESymbol == None:
      logging.error('%s: Could not get quotes for option symbols', self.getName())
      return

    self.generateTrade(ATMPlus50CESymbol, numLots, quoteATMPlus50CESymbol.lastTradedPrice)
    self.generateTrade(ATMMinus50PESymbol, numLots, quoteATMMinus50PESymbol.lastTradedPrice)
    logging.info('%s: Trades generated.', self.getName())
    # add symbols to created list
    self.tradesCreatedSymbols.append(ATMPlus50CESymbol)
    self.tradesCreatedSymbols.append(ATMMinus50PESymbol)

  def generateTrade(self, optionSymbol, numLots, lastTradedPrice):
    trade = Trade(optionSymbol)
    trade.strategy = self.getName()
    trade.isOptions = True
    trade.direction = Direction.SHORT # Always short here as option selling only
    trade.productType = self.productType
    trade.placeMarketOrder = True
    trade.requestedEntry = lastTradedPrice
    trade.timestamp = Utils.getEpoch(self.startTimestamp) # setting this to strategy timestamp
    
    isd = Instruments.getInstrumentDataBySymbol(optionSymbol) # Get instrument data to know qty per lot
    trade.qty = isd['lot_size'] * numLots
    
    trade.stopLoss = Utils.roundToNSEPrice(trade.requestedEntry + trade.requestedEntry * self.slPercentage / 100)
    trade.target = 0 # setting to 0 as no target is applicable for this trade

    trade.intradaySquareOffTimestamp = Utils.getEpoch(self.squareOffTimestamp)
    # Hand over the trade to TradeManager
    TradeManager.addNewTrade(trade)

  def shouldPlaceTrade(self, trade, tick):
    # First call base class implementation and if it returns True then only proceed
    if super().shouldPlaceTrade(trade, tick) == False:
      return False
    # We dont have any condition to be checked here for this strategy just return True
    return True
