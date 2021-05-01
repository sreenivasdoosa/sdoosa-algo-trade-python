from flask.views import MethodView
import json
import logging
from core.Controller import Controller

class HoldingsAPI(MethodView):
  def get(self):
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    holdings = brokerHandle.holdings()
    logging.info('User holdings => %s', holdings)
    return json.dumps(holdings)
  