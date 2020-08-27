import json
from config import getUserConfig, getServerConfig, getSystemConfig
from flask import Flask, render_template, request, redirect
from zerodha import loginZerodha, getKite
from algo import startAlgo
import logging
import threading
import time
from instruments import fetchInstruments, getInstrumentDataBySymbol

app = Flask(__name__)
app.config['DEBUG'] = True

def initLoggingConfg():
  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

@app.route('/', methods=['GET'])
def home():
  if 'loggedIn' in request.args and request.args['loggedIn'] == 'true':
    return render_template('index_loggedin.html')
  elif 'algoStarted' in request.args and request.args['algoStarted'] == 'true':
    return render_template('index_algostarted.html')
  else:
    return render_template('index.html')
  
@app.route('/apis/broker/login/zerodha', methods=['GET'])
def login_broker():
  return loginZerodha(request.args)

@app.route('/apis/algo/start', methods=['POST'])
def start_algo():
  x = threading.Thread(target=startAlgo)
  x.start()
  systemConfig = getSystemConfig()
  homeUrl = systemConfig['homeUrl'] + '?algoStarted=true'
  logging.info('Sending redirect url %s in response', homeUrl)
  respData = { 'redirect': homeUrl }
  return json.dumps(respData)

@app.route('/positions', methods=['GET'])
def positions():
  kite = getKite()
  positions = kite.positions()
  print('getKite positions => ', positions)
  return json.dumps(positions)

@app.route('/holdings', methods=['GET'])
def holdings():
  kite = getKite()
  holdings = kite.holdings()
  print('getKite holdings => ', holdings)
  return json.dumps(holdings)


# Execution starts here
initLoggingConfg()

serverConfig = getServerConfig()
logging.info('serverConfig => %s', serverConfig)

userConfig = getUserConfig()
logging.info('userConfig => %s', userConfig)

port = serverConfig['port'] 

app.run('localhost', port)