import logging
from smartapi import SmartConnect

from config.Config import getSystemConfig
from loginmgmt.BaseLogin import BaseLogin

class AngelOneLogin(BaseLogin):
  def __init__(self, brokerAppDetails):
    BaseLogin.__init__(self, brokerAppDetails)

  def login(self, args):
    logging.info('==> AngelOneLogin .args => %s', args);
    systemConfig = getSystemConfig()
    brokerHandle = SmartConnect(api_key=self.brokerAppDetails.appKey)
    redirectUrl = None
    session = brokerHandle.generateSession(self.brokerAppDetails.clientID,self.brokerAppDetails.password,self.brokerAppDetails.totp)
    logging.info('AngelOneLogin session = %s', session)
    accessToken = brokerHandle.getAccessToken()
    logging.info('AngelOneLogin Login successful. accessToken = %s', accessToken)

    # set broker handle and access token to the instance
    self.setBrokerHandle(brokerHandle)
    self.setAccessToken(accessToken)

    # redirect to home page with query param loggedIn=true
    homeUrl = systemConfig['homeUrl'] + '?loggedIn=true'
    logging.info('AngelOneLogin Redirecting to home page %s', homeUrl)
    redirectUrl = homeUrl
    
    return redirectUrl

