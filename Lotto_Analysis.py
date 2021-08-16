import os
import json
import requests
import base64
import re
import platform
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
import telegram
#from telegram.ext import Updater, CommandHandler

import re
import collections
import time

from MSSQL_Connector import MSSQL_Connector


class ChromeBrowserController():
    def __init__(self):
        self.cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.ChromeDriverFile = os.path.join(self.cur_dir, "./chromedriver.exe")
        self.ChromeDriver = webdriver.Chrome(self.ChromeDriverFile)

    def connectURL(self, URL):
        self.ChromeDriver.implicitly_wait(3)
        self.ChromeDriver.get(URL)
        self.ChromeDriver.implicitly_wait(3)

    def findElement_By_ClassName(self, className):
        return self.ChromeDriver.find_element("class name", className)

class Lotto():
    def __init__(self):
        #로또 정보
        self.LottoIndex = 0
        self.LottoStartWinningRounds = 1
        self.LottoStartDate = datetime(2002, 12, 7)
        self.LottoWinTermDays = 7
        self.LottoURL = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="

        self.ChromeBC = ChromeBrowserController()

    def getDateTimeByWinningRounds(self, WinningRounds):
        WinningRounds = WinningRounds - 1
        if(WinningRounds < 0):
            return 0

        return self.LottoStartDate + timedelta(days = (WinningRounds*self.LottoWinTermDays))

    def getCurrentWinningRounds(self):
        rounds = ((datetime.now() - self.LottoStartDate).days / self.LottoWinTermDays) + 1
        return int(rounds)

    def getLottoWinningNumbers(self, WinningRounds):
        if(self.getCurrentWinningRounds() < WinningRounds):
            return 0

        connURL = self.LottoURL + str(WinningRounds)
        self.ChromeBC.connectURL(connURL)
        Numbers = self.ChromeBC.findElement_By_ClassName('nums').text
        Numbers = re.findall("\d+", Numbers)

        Numbers = list(map(int, Numbers))

        WinningNumbers = Numbers[0:6]
        BonusNumber = Numbers[6]

        return WinningNumbers, BonusNumber


LottoInfo = Lotto()
MSSQL_Connect = MSSQL_Connector()
MSSQL_Connect.ConnectDB("localhost", 1433, "sa", "qksksk153", "WEB_DB", "utf8", True)

arg = []

row = MSSQL_Connect.SP_LOTTO_MAX_GET_INFO()

db_Winning_Rounds_Max = row["WINNING_ROUNDS"]

if db_Winning_Rounds_Max < LottoInfo.getCurrentWinningRounds():
    db_Winning_Rounds_Max = db_Winning_Rounds_Max + 1

    for rounds in range(db_Winning_Rounds_Max, LottoInfo.getCurrentWinningRounds() + 1):
        arg = []
        arg.append(rounds)
        win, bonus = LottoInfo.getLottoWinningNumbers(rounds)

        arg += win
        arg.append(bonus)
        sDate = LottoInfo.getDateTimeByWinningRounds(rounds).isoformat()
        arg.append(sDate)

        MSSQL_Connect.SP_LOTTO_UPDATE_INFO(arg)

        print(rounds)

        time.sleep(2)

else:
    print("입력할거 없음.")