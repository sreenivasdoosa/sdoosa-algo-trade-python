import logging

from instruments.Instruments import Instruments
from Test import Test

class Algo:
  isAlgoRunning = None

  @staticmethod
  def startAlgo():
    if Algo.isAlgoRunning == True:
      logging.info("Algo has already started..")
      return
    
    logging.info("Starting Algo...")
    Instruments.fetchInstruments()

    Algo.isAlgoRunning = True
    logging.info("Algo started.")
    Test.testTicker()
    #Test.testOrders()
    
    

