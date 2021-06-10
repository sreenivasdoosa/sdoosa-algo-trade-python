import logging
import os
import socket
import struct
import time

from tvDatafeed import TvDatafeed, Interval

from config.Config import getTVloginConfig
from utils.Utils import Utils


# nse_list = pd.read_csv("ind_nifty500list.csv")
# print(nse_list)
class indexTicker:
    @staticmethod
    def run():
        if Utils.isTodayHoliday():
            logging.info("indexTicker: Not Starting as Today is Trading Holiday.")
            return
        if Utils.isMarketClosedForTheDay():
            logging.info("indexTicker: Not Starting  as Market is closed for the day.")
            return

        tvLoginCredentials = getTVloginConfig()
        logging.info('indexTicker: TV Ticker Login Details => %s', tvLoginCredentials)
        tv = TvDatafeed(tvLoginCredentials['username'], tvLoginCredentials['password'], chromedriver_path=None)
        dir = indexTicker.createfolder(tvLoginCredentials['logPath'])
        Utils.waitTillMarketOpens("indexTicker")
        # #testing...
        # time.sleep(60.0 - ((time.time()) % 60.0))
        # track and update ticks in a loop
        time.sleep((60.0 - ((indexTicker.RequestTimefromNtp()) % 60.0)) + 4)
        print(time.ctime())
        counter = 0
        while True:
            if Utils.isMarketClosedForTheDay() and (counter == 0):  # counter to ensure 3:30 candle is recorded.
                counter = 1
            elif Utils.isMarketClosedForTheDay() and (counter == 1):
                logging.info('indexTicker: Stopping as market closed.')
                break
            try:
                niftySpot = indexTicker.tvTickerhist(tv, "NIFTY", "1min")
                niftyFut = indexTicker.tvTickerhist(tv, "NIFTY1!", "1min")
                bankniftySpot = indexTicker.tvTickerhist(tv, "BANKNIFTY", "1min")
                bankniftyFut = indexTicker.tvTickerhist(tv, "BANKNIFTY1!", "1min")
                indexTicker.logCSV(niftySpot, "NIFTY", dir)
                indexTicker.logCSV(niftyFut, "NIFTY1", dir)
                indexTicker.logCSV(bankniftySpot, "BANKNIFTY", dir)
                indexTicker.logCSV(bankniftyFut, "BANKNIFTY1", dir)
                logging.info('indexTicker: logged 1min ticker....%s', time.asctime(time.localtime(time.time())))
                time.sleep((60.0 - ((time.time()) % 60.0)) + 2)
            except Exception as e:
                logging.exception("indexTicker: Main thread exemption")

    @staticmethod
    def tvTickerhist(tv, symbol, interval):
        if (interval == "1min"):
            data = tv.get_hist(symbol=symbol, exchange='NSE', interval=Interval.in_1_minute, n_bars=2)
        return data

    @staticmethod
    def logCSV(data, file, dir):
        data = data.reset_index()
        data["date"] = data["datetime"].dt.date
        data["time"] = data["datetime"].dt.time
        data.drop("datetime", axis='columns', inplace=True)
        data['symbol'] = data['symbol'].str.replace('NSE:', '')
        data = data[["date", "time", "symbol", "open", "high", "low", "close", "volume"]]
        data = data[data.index.isin([0, 0])]  # consider only the last 1min array
        data.to_csv(dir + "/" + file + ".csv", index=False, header=False, mode='a')

    @staticmethod
    def createfolder(path):
        # check and create directory for today`s date
        intradayTradesDir = os.path.join(path, Utils.getTodayDateStr())
        if os.path.exists(intradayTradesDir) == False:
            logging.info('indexTicker: Intraday Directory %s does not exist. Hence going to create.',
                         intradayTradesDir)
            os.makedirs(intradayTradesDir)
        return intradayTradesDir

    @staticmethod
    def RequestTimefromNtp(addr='time.windows.com'):
        REF_TIME_1970 = 2208988800  # Reference time
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = b'\x1b' + 47 * b'\0'
        client.sendto(data, (addr, 123))
        data, address = client.recvfrom(1024)
        if data:
            t = struct.unpack('!12I', data)[10]
            t -= REF_TIME_1970
        return t
