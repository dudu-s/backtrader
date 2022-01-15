from datetime import date
import datetime
import csv
import os.path
import sys
import pandas as pd

class OptionsLoader:
    CALL = 0
    PUT = 1

    # type = 0: call, 1:put
    def Load(self, symbol, startDate, strikeToLoad, expirationDateToLoad, type):
        
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, '../../OptionsPrices')

        lstData = []
        lstIndex = []
        header = True
        rowsperday = 3
        firstFill = False
        with open(os.path.join(datapath,symbol)  + '.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                if header == False:
                    tradeDate   = datetime.datetime.strptime(row[1],'%Y-%m-%d')
                    expirDate   = datetime.datetime.strptime(row[2],'%Y-%m-%d').date()
                    dte         = row[3]
                    strike      = float(row[4])
                    stockPrice  = row[5]

                    if type == self.CALL:
                        volume      = float(row[6])
                        bidSize     = row[8]
                        askSize     = row[9]
                        bidPrice    = row[14]
                        askPrice    = row[16]
                    else:
                        volume      = float(row[10])
                        bidSize     = row[12]
                        askSize     = row[13]
                        bidPrice    = row[18]
                        askPrice    = row[20]

                    if expirationDateToLoad == expirDate and strikeToLoad == strike:
                        if not firstFill:
                            firstFill = True
                            delta = (tradeDate - startDate).days
                            for day in range (0,delta):
                                startTime = startDate + datetime.timedelta(hours = 9) + datetime.timedelta(days = day)
                                self.addData(lstData, lstIndex, askPrice, bidPrice, startTime, rowsperday)

                        
                        self.addData(lstData, lstIndex, askPrice, bidPrice, tradeDate, rowsperday)
                            
                header = False
        
        # Fill zero prices after the options had expired
        delta = (datetime.datetime.now() - lstIndex[-1]).days
        for day in range (0,delta):
            startTime = lstIndex[-1] + datetime.timedelta(days = 1)
            self.addData(lstData, lstIndex, 0, 0, startTime, rowsperday)

        return self.transformToPanda(lstData, lstIndex)
    
    def transformToPanda(self, lstData, lstIndex):
        df_list = list()
        df_list.clear()
    
        data = pd.DataFrame(lstData, index=lstIndex, columns =['Open','High','Low','Close','Adj Close','Volume'])

        return data
    
    def addData(self, lstData, lstIndex, askPrice, bidPrice, tradeTime, rowsperday):
        for minute in range(0,rowsperday):
            startTime = tradeTime + (datetime.timedelta(minutes = 20) * minute)
            lstData.append([float(askPrice), 
                                    float(askPrice), 
                                    float(bidPrice), 
                                    float(askPrice), 
                                    float(askPrice), 
                                    1000*1000])
            lstIndex.append(startTime)

if __name__ == '__main__':
    # For testing purposes only!
    OptionsLoader().Load('CRTX', datetime.date(2017,1,1), 60, datetime.date(2021,11,19), OptionsLoader.CALL)