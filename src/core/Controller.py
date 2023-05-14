import logging

from config.Config import getBrokerAppConfig
from models.BrokerAppDetails import BrokerAppDetails
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from loginmgmt.AngelOneLogin import AngelOneLogin

class Controller:
  brokerLogin = None # static variable
  brokerName = None # static variable
  brokerAppDetails = None

  def handleBrokerLogin(args,kwargs):
    broker = kwargs['broker']
    logging.info('broker name %s', broker)
    Controller.brokerName = broker
    brokerAppConfig = getBrokerAppConfig()[broker]
    logging.info('handleBrokerLogin kwargs %s', kwargs)
    
    if Controller.brokerName == 'zerodha':
      brokerAppDetails = BrokerAppDetails(broker)
      brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
      brokerAppDetails.setAppSecret(brokerAppConfig['appSecret'])
      brokerAppDetails.setClientID(brokerAppConfig['clientID'])
      
      instrumentKeys = BrokerAppDetails.InstrumentKeys()
      instrumentKeys.setTradingSymbol(brokerAppConfig['instrumentKeys']['tradingSymbol'])
      instrumentKeys.setInstrumentToken(brokerAppConfig['instrumentKeys']['instrumentToken'])
      brokerAppDetails.setInstrumentKeys(instrumentKeys)
      Controller.brokerLogin = ZerodhaLogin(brokerAppDetails)
      Controller.brokerAppDetails = brokerAppDetails
    #For AngelOne broker
    elif Controller.brokerName == 'angel':
      brokerAppDetails = BrokerAppDetails(broker)
      brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
      brokerAppDetails.setClientID(kwargs['clientId'])
      brokerAppDetails.setPassword(kwargs['password'])
      brokerAppDetails.setTOTP(kwargs['totp'])
      instrumentKeys = BrokerAppDetails.InstrumentKeys()
      instrumentKeys.setTradingSymbol(brokerAppConfig['instrumentKeys']['tradingSymbol'])
      instrumentKeys.setInstrumentToken(brokerAppConfig['instrumentKeys']['instrumentToken'])
      brokerAppDetails.setInstrumentKeys(instrumentKeys)
      Controller.brokerLogin = AngelOneLogin(brokerAppDetails)
      Controller.brokerAppDetails = brokerAppDetails
      
    redirectUrl = Controller.brokerLogin.login(args)
    return redirectUrl

  def getBrokerLogin():
    return Controller.brokerLogin

  def getBrokerName():
    return Controller.brokerName

  def getBrokerAppDetails():
    return Controller.brokerAppDetails
