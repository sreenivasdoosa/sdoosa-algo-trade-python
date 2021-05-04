import logging
import threading

from instruments.Instruments import Instruments
from trademgmt.TradeManager import TradeManager

from strategies.SampleStrategy import SampleStrategy

#from Test import Test

class Algo:
  isAlgoRunning = None

  @staticmethod
  def startAlgo():
    if Algo.isAlgoRunning == True:
      logging.info("Algo has already started..")
      return
    
    logging.info("Starting Algo...")
    Instruments.fetchInstruments()

    # start trade manager in a separate thread
    tm = threading.Thread(target=TradeManager.init)
    tm.start()

    # start running strategies: Run each strategy in a separate thread
    threading.Thread(target=SampleStrategy.getInstance().run).start()
    
    Algo.isAlgoRunning = True
    logging.info("Algo started.")
    #Test.testTicker()
    #Test.testOrders()
    
    

