import logging
from zerodha import getKite
from instruments import fetchInstruments
from quotes import getCMP
from orders import placeOrder, modifyOrder, placeSLOrder, cancelOrder
from utils import roundToNSEPrice
from ticker import startTicker, stopTicker, registerSymbols
import time
import threading

def startAlgo():
  logging.info("Algo started...")
  kite = getKite()
  fetchInstruments(kite)

  #testOrders()
  testTicker()

def testTicker():
  startTicker()
  # sleep for 5 seconds and register trading symbols to receive ticks
  time.sleep(5)
  registerSymbols(['SBIN', 'RELIANCE'])

  time.sleep(5)
  exchange = 'NSE';
  tradingSymbol = 'SBIN'
  lastTradedPrice = getCMP(exchange + ':' + tradingSymbol)
  logging.info(tradingSymbol + ' CMP = %f', lastTradedPrice)
  qty = 1
  direction = 'SHORT'

  orderId = placeOrder(tradingSymbol, lastTradedPrice, qty, direction)
  logging.info('placed order: order id = %s', orderId)

  # wait for 120 seconds and stop ticker service
  time.sleep(120)
  logging.info('Going to stop ticker')
  stopTicker()

def testOrders():
  exchange = 'NSE';
  tradingSymbol = 'SBIN'
  lastTradedPrice = getCMP(exchange + ':' + tradingSymbol)
  logging.info(tradingSymbol + ' CMP = %f', lastTradedPrice)

  limitPrice = lastTradedPrice - lastTradedPrice * 1 / 100
  limitPrice = roundToNSEPrice(limitPrice)
  qty = 1
  direction = 'LONG'

  # place order
  origOrderId = placeOrder(tradingSymbol, limitPrice, qty, direction)
  logging.info('Original order Id %s', origOrderId)

  # sleep for 10 seconds then modify order
  time.sleep(10)
  newPrice = lastTradedPrice
  modifyOrder(origOrderId, newPrice)

  # sleep for 10 seconds and then place SL order
  time.sleep(10)
  slPrice = newPrice - newPrice * 1 / 100
  slPrice = roundToNSEPrice(slPrice)
  slDirection = 'SHORT' if direction == 'LONG' else 'LONG'
  slOrderId = placeSLOrder(tradingSymbol, slPrice, qty, slDirection)
  logging.info('SL order Id %s', slOrderId)

  # sleep for 10 seconds and then place target order
  time.sleep(10)
  targetPrice = newPrice + newPrice * 2 / 100
  targetPrice = roundToNSEPrice(targetPrice)
  targetDirection = 'SHORT' if direction == 'LONG' else 'LONG'
  targetOrderId = placeOrder(tradingSymbol, targetPrice, qty, targetDirection)
  logging.info('Target order Id %s', targetOrderId)

  # sleep for 10 seconds and cancel target order
  time.sleep(10)
  cancelOrder(targetOrderId)
  logging.info('Cancelled Target order Id %s', targetOrderId)

  logging.info("Algo done executing all orders. Check ur orders and positions in broker terminal.")


