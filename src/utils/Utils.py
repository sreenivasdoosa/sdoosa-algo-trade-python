import math
import uuid
import time
import logging
import calendar
from datetime import datetime

from config.Config import getHolidays

class Utils:
  dateFormat = "%Y-%m-%d"
  timeFormat = "%H:%M:%S"
  dateTimeFormat = "%Y-%m-%d %H:%M:%S"

  @staticmethod
  def initLoggingConfig():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

  @staticmethod
  def roundOff(price): # Round off to 2 decimal places
    return round(price, 2)
    
  @staticmethod
  def roundToNSEPrice(price):
    x = round(price, 2) * 20
    y = math.ceil(x)
    return y / 20

  @staticmethod
  def isMarketOpen():
    if Utils.isTodayHoliday():
      return False
    now = datetime.now()
    marketStartTime = Utils.getMarketStartTime()
    marketEndTime = Utils.getMarketEndTime()
    return now >= marketStartTime and now <= marketEndTime

  @staticmethod
  def isMarketClosedForTheDay():
    # This method returns true if the current time is > marketEndTime
    # Please note this will not return true if current time is < marketStartTime on a trading day
    if Utils.isTodayHoliday():
      return True
    now = datetime.now()
    marketEndTime = Utils.getMarketEndTime()
    return now > marketEndTime

  @staticmethod
  def waitTillMarketOpens(context):
    nowEpoch = Utils.getEpoch(datetime.now())
    marketStartTimeEpoch = Utils.getEpoch(Utils.getMarketStartTime())
    waitSeconds = marketStartTimeEpoch - nowEpoch
    if waitSeconds > 0:
      logging.info("%s: Waiting for %d seconds till market opens...", context, waitSeconds)
      time.sleep(waitSeconds)

  @staticmethod
  def getEpoch(datetimeObj):
    # This method converts given datetimeObj to epoch seconds
    epochSeconds = datetime.timestamp(datetimeObj)
    return int(epochSeconds) # converting double to long

  @staticmethod
  def getMarketStartTime():
    return Utils.getTimeOfToDay(9, 15, 0)

  @staticmethod
  def getMarketEndTime():
    return Utils.getTimeOfToDay(15, 30, 0)

  @staticmethod
  def getTimeOfToDay(hours, minutes, seconds):
    datetimeObj = datetime.now()
    datetimeObj = datetimeObj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    return datetimeObj

  @staticmethod
  def getTodayDateStr():
    now = datetime.now()
    return now.strftime(Utils.dateFormat)

  @staticmethod
  def isTodayHoliday():
    now = datetime.now()
    dayOfWeek = calendar.day_name[now.weekday()]
    if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
      return True

    todayDate = Utils.getTodayDateStr()
    holidays = getHolidays()
    if (todayDate in holidays):
      return True
    else:
      return False

  @staticmethod
  def generateTradeID():
    return uuid.uuid4()

