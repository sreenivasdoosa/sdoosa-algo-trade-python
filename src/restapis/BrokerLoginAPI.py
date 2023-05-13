import logging
from flask.views import MethodView
from flask import request, redirect

from core.Controller import Controller 

class BrokerLoginAPI(MethodView):
  def get(self,**kwargs):
    logging.info('BrokerLoginAPI args %s', kwargs)
    redirectUrl = Controller.handleBrokerLogin(request.args,kwargs)
    return redirect(redirectUrl, code=302)

  def post(self,**kwargs):
    logging.info('BrokerLoginAPI args %s', kwargs)
    logging.info('POST request %s', request)
    kwargs['clientId']=request.form.get('clientId')
    kwargs['password']=request.form.get('psw')
    kwargs['totp']=request.form.get('totp')
    redirectUrl = Controller.handleBrokerLogin(request.args,kwargs)
    return redirect(redirectUrl, code=302)