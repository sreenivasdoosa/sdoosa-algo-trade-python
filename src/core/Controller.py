import logging

from config.Config import getBrokerAppConfig
from models.BrokerAppDetails import BrokerAppDetails
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from loginmgmt.AngelOneLogin import AngelOneLogin

class Controller:
  brokerLogin = None # static variable
  brokerName = None # static variable

  def handleBrokerLogin(args,kwargs):
    broker = kwargs['broker']
    brokerAppConfig = getBrokerAppConfig()
    brokerAppDetails = BrokerAppDetails(broker)
    brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
    brokerAppDetails.setAppSecret(brokerAppConfig['appSecret'])

    logging.info('handleBrokerLogin kwargs %s', kwargs)
    logging.info('handleBrokerLogin appKey %s', brokerAppDetails.appKey)
    logging.info('broker name %s', broker)
    Controller.brokerName = broker
    if Controller.brokerName == 'zerodha':
      brokerAppDetails.setClientID(brokerAppConfig['clientID'])
      Controller.brokerLogin = ZerodhaLogin(brokerAppDetails)
    #For AngelOne broker
    elif Controller.brokerName == 'angel':
      brokerAppDetails.setClientID(kwargs['clientId'])
      brokerAppDetails.setPassword(kwargs['password'])
      brokerAppDetails.setTOTP(kwargs['totp'])
      Controller.brokerLogin = AngelOneLogin(brokerAppDetails)

    redirectUrl = Controller.brokerLogin.login(args)
    return redirectUrl

  def getBrokerLogin():
    return Controller.brokerLogin

  def getBrokerName():
    return Controller.brokerName
