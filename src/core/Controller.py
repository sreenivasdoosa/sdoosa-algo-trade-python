import logging

from config.Config import getBrokerAppConfig
from models.BrokerAppDetails import BrokerAppDetails
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from loginmgmt.AngelOneLogin import AngelOneLogin

class Controller:
  brokerLogin = None # static variable
  brokerName = None # static variable

  def handleBrokerLogin(args,kwargs):
    brokerAppConfig = getBrokerAppConfig()

    brokerAppDetails = BrokerAppDetails(brokerAppConfig['broker'])
    brokerAppDetails.setClientID(brokerAppConfig['clientID'])
    brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
    brokerAppDetails.setAppSecret(brokerAppConfig['appSecret'])

    logging.info('handleBrokerLogin kwargs %s', kwargs)
    broker = kwargs['broker']
    logging.info('handleBrokerLogin appKey %s', brokerAppDetails.appKey)
    logging.info('broker name %s', broker)
    Controller.brokerName = broker
    if Controller.brokerName == 'zerodha':
      Controller.brokerLogin = ZerodhaLogin(brokerAppDetails)
    # Other brokers - not implemented
    elif Controller.brokerName == 'angel':
      Controller.brokerLogin = AngelOneLogin(brokerAppDetails,kwargs)

    redirectUrl = Controller.brokerLogin.login(args)
    return redirectUrl

  def getBrokerLogin():
    return Controller.brokerLogin

  def getBrokerName():
    return Controller.brokerName
