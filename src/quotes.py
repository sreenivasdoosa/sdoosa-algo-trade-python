from zerodha import getKite

def getCMP(tradingSymbol):
  kite = getKite()
  quote = kite.quote(tradingSymbol)
  if quote:
    return quote[tradingSymbol]['last_price']
  else:
    return 0