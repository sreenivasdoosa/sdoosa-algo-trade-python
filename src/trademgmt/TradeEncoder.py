
from json import JSONEncoder

class TradeEncoder(JSONEncoder):
  def default(self, o):
    return o.__dict__