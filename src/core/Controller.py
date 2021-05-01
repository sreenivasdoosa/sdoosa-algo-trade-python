import logging

from config.Config import getBrokerAppConfig
from models.BrokerAppDetails import BrokerAppDetails
from loginmgmt.ZerodhaLogin import ZerodhaLogin

class Controller:
  brokerLogin = None # static variable

  def handleBrokerLogin(args):
    brokerAppConfig = getBrokerAppConfig()

    brokerAppDetails = BrokerAppDetails(brokerAppConfig['broker'])
    brokerAppDetails.setClientID(brokerAppConfig['clientID'])
    brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
    brokerAppDetails.setAppSecret(brokerAppConfig['appSecret'])

    logging.info('handleBrokerLogin appKey %s', brokerAppDetails.appKey)

    if brokerAppDetails.broker == 'zerodha':
      Controller.brokerLogin = ZerodhaLogin(brokerAppDetails)
    # Other brokers - not implemented
    #elif brokerAppDetails.broker == 'fyers':
      #Controller.brokerLogin = FyersLogin(brokerAppDetails)

    redirectUrl = Controller.brokerLogin.login(args)
    return redirectUrl

  def getBrokerLogin():
    return Controller.brokerLogin
