import logging
import threading
import time

from instruments.Instruments import Instruments
from trademgmt.TradeManager import TradeManager
from datamgmt.DataManager import DataManager

from strategies.SampleStrategy import SampleStrategy
from strategies.BNFORB30Min import BNFORB30Min
from strategies.OptionSelling import OptionSelling
from strategies.ShortStraddleBNF import ShortStraddleBNF

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

    #dm = threading.Thread(target=DataManager.run,args=(1,))
    #dm.start()

    # sleep for 2 seconds for DataManager to get initialized
    #time.sleep(2)

    # start trade manager in a separate thread
    tm = threading.Thread(target=TradeManager.run,args=(5,))
    tm.start()

    # sleep for 2 seconds for TradeManager to get initialized
    time.sleep(2)

    # start running strategies: Run each strategy in a separate thread
    threading.Thread(target=SampleStrategy.getInstance().run).start()
    #threading.Thread(target=BNFORB30Min.getInstance().run).start()
    #threading.Thread(target=OptionSelling.getInstance().run).start()
    #threading.Thread(target=ShortStraddleBNF.getInstance().run).start()
    
    Algo.isAlgoRunning = True
    logging.info("Algo started.")
