import json

def getServerConfig():
  with open('../config/server.json', 'r') as server:
    jsonServerData = json.load(server)
    return jsonServerData

def getSystemConfig():
  with open('../config/system.json', 'r') as system:
    jsonSystemData = json.load(system)
    return jsonSystemData

def getBrokerAppConfig():
  with open('../config/brokerapp.json', 'r') as brokerapp:
    jsonUserData = json.load(brokerapp)
    return jsonUserData

def getHolidays():
  with open('../config/holidays.json', 'r') as holidays:
    holidaysData = json.load(holidays)
    return holidaysData
    