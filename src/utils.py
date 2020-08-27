import math

def roundToNSEPrice(price):
  x = round(price, 2) * 20
  y = math.ceil(x)
  return y / 20
