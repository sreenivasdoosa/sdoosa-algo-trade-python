import os
import logging
from flask import Flask

from config.Config import getBrokerAppConfig, getServerConfig, getSystemConfig
from restapis.HomeAPI import HomeAPI
from restapis.BrokerLoginAPI import BrokerLoginAPI
from restapis.StartAlgoAPI import StartAlgoAPI
from restapis.PositionsAPI import PositionsAPI
from restapis.HoldingsAPI import HoldingsAPI

app = Flask(__name__)
app.config['DEBUG'] = True

app.add_url_rule("/", view_func=HomeAPI.as_view("home_api"))
app.add_url_rule("/apis/broker/login/zerodha", view_func=BrokerLoginAPI.as_view("broker_login_api"))
app.add_url_rule("/apis/algo/start", view_func=StartAlgoAPI.as_view("start_algo_api"))
app.add_url_rule("/positions", view_func=PositionsAPI.as_view("positions_api"))
app.add_url_rule("/holdings", view_func=HoldingsAPI.as_view("holdings_api"))

def initLoggingConfg(filepath):
  format = "%(asctime)s: %(message)s"
  logging.basicConfig(filename=filepath, format=format, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

# Execution starts here
serverConfig = getServerConfig()

deployDir = serverConfig['deployDir']
if os.path.exists(deployDir) == False:
  print("Deploy Directory " + deployDir + " does not exist. Exiting the app.")
  exit(-1)

logFileDir = serverConfig['logFileDir']
if os.path.exists(logFileDir) == False:
  print("LogFile Directory " + logFileDir + " does not exist. Exiting the app.")
  exit(-1)

print("Deploy  Directory = " + deployDir)
print("LogFile Directory = " + logFileDir)
initLoggingConfg(logFileDir + "/app.log")

logging.info('serverConfig => %s', serverConfig)

brokerAppConfig = getBrokerAppConfig()
logging.info('brokerAppConfig => %s', brokerAppConfig)

port = serverConfig['port']

app.run('localhost', port)