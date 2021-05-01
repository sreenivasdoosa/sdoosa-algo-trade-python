import math
import logging

class Utils:
  @staticmethod
  def initLoggingConfig():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

  @staticmethod
  def roundToNSEPrice(price):
    x = round(price, 2) * 20
    y = math.ceil(x)
    return y / 20