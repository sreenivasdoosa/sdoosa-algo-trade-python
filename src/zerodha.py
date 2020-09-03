import logging
from kiteconnect import KiteConnect
from config import getUserConfig, getSystemConfig
from flask import redirect
from instruments import fetchInstruments
import threading

kite = None
accessToken = None
def getKite():
  return kite

def getAccessToken():
  return accessToken

def loginZerodha(args):
  userConfig = getUserConfig()
  systemConfig = getSystemConfig()
  global kite
  global accessToken
  kite = KiteConnect(api_key=userConfig['apiKey'])
  if 'request_token' in args:
    requestToken = args['request_token']
    logging.info('requestToken = %s', requestToken)
    session = kite.generate_session(requestToken, api_secret=userConfig['apiSecret'])
    accessToken = session['access_token']
    logging.info('accessToken = %s', accessToken)
    kite.set_access_token(accessToken)
    logging.info('Login successful. accessToken = %s', accessToken)
    # redirect to home page with query param loggedIn=true
    homeUrl = systemConfig['homeUrl'] + '?loggedIn=true'
    logging.info('Redirecting to home page %s', homeUrl)

    return redirect(homeUrl, code=302)
  else:
    loginUrl = kite.login_url()
    logging.info('Redirecting to zerodha login url = %s', loginUrl)
    return redirect(loginUrl, code=302)

