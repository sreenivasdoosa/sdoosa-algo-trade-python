import logging
from kiteconnect import KiteConnect
from config import getUserConfig
from flask import redirect

kite = None
def getKite():
  return kite

def loginZerodha(args):
  userConfig = getUserConfig()
  global kite
  kite = KiteConnect(api_key=userConfig['apiKey'])
  if 'request_token' in args:
    requestToken = args['request_token']
    print('requestToken = ' + requestToken)
    session = kite.generate_session(requestToken, api_secret=userConfig['apiSecret'])
    accessToken = session['access_token']
    print('accessToken = ' + accessToken)
    kite.set_access_token(accessToken)
    holdings = kite.holdings()
    print('holdings => ', holdings)
    return '<p>Login successful. accessToken = ' + accessToken + '</p>'
  else:
    loginUrl = kite.login_url()
    print('login url => ' + loginUrl)
    return redirect(loginUrl, code=302)

