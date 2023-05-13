import logging
from smartapi import SmartConnect

from config.Config import getSystemConfig
from loginmgmt.BaseLogin import BaseLogin

class AngelOneLogin(BaseLogin):
  def __init__(self, brokerAppDetails,kwargs):
    BaseLogin.__init__(self, brokerAppDetails, kwargs)

  def login(self, args):
    logging.info('==> AngelOneLogin .args => %s', args);
    logging.info('==> AngelOneLogin .kwargs => %s', self.kwargs);
    systemConfig = getSystemConfig()
    brokerHandle = SmartConnect(api_key=self.brokerAppDetails.appKey)
    redirectUrl = None
    session = brokerHandle.generateSession(self.kwargs['clientId'],self.kwargs['password'],self.kwargs['totp'])
    logging.info('AngelOneLogin session = %s', session)
    accessToken = session['data']['jwtToken']
    logging.info('AngelOneLogin accessToken = %s', accessToken)
    brokerHandle.setAccessToken(accessToken)
    
    logging.info('AngelOneLogin Login successful. accessToken = %s', accessToken)

    # set broker handle and access token to the instance
    self.setBrokerHandle(brokerHandle)
    self.setAccessToken(accessToken)

    # redirect to home page with query param loggedIn=true
    homeUrl = systemConfig['homeUrl'] + '?loggedIn=true'
    logging.info('AngelOneLogin Redirecting to home page %s', homeUrl)
    redirectUrl = homeUrl
    

    return redirectUrl

