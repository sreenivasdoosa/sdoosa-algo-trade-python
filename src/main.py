from config import *
from flask import Flask, render_template, request
from zerodha import loginZerodha, getKite

serverConfig = getServerConfig()
print('serverConfig => ', serverConfig)

userConfig = getUserConfig()
print('userConfig => ', userConfig)

port = serverConfig['port'] 

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/', methods=['GET'])
def home():
  return render_template('index.html')

@app.route('/apis/broker/login/zerodha', methods=['GET'])
def login_broker():
  return loginZerodha(request.args)

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


app.run('localhost', port)