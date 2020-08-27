import json

def getServerConfig():
  with open('../config/server.json', 'r') as server:
    jsonServerData = json.load(server)
    return jsonServerData

def getSystemConfig():
  with open('../config/system.json', 'r') as system:
    jsonSystemData = json.load(system)
    return jsonSystemData

def getUserConfig():
  with open('../config/user.json', 'r') as user:
    jsonUserData = json.load(user)
    return jsonUserData
    