from time import strftime, strptime
from numpy import unicode_
import yfinance as yf
import sys
import os
import datetime
import csv
import os.path
import pandas as pd

class AbstractDataProviderBuilder:
    def getData(self, ticker, startDate):
        pass

    def transformToPanda(self, lstData, lstIndex):
        df_list = list()
        df_list.clear()
    
        data = pd.DataFrame(lstData, index=lstIndex, columns =['Open','High','Low','Close','Adj Close','Volume'])
        df_list.append(data)
        return df_list
        

class AbstractCSVDataProviderBuilder(AbstractDataProviderBuilder):
    filepath : str

    def __init__(self):
        super(AbstractCSVDataProviderBuilder, self).__init__()
        self.filepath = "C:/PythonScripts/Projects/BackTrader/ExternalDataSources"

    def getData(self, ticker, startDate):
        pass

# Data Provider = 1
class YahooDataProviderBuilder(AbstractDataProviderBuilder):
    def getData(self, ticker, startDate):

        df_list = list()
        df_list.clear()

        data = yf.download(ticker, group_by="Ticker", start=startDate, end=datetime.datetime.now().strftime("%Y-%m-%d"), interval="1d")
        df_list.append(data)
        return df_list

class GenericCSVProviderBuilder(AbstractCSVDataProviderBuilder):
    headerCount : int
    dateIndex : int
    closeIndex: int
    openIndex : int
    lowIndex  : int
    highIndex : int
    volumeIndex :int
    reversedOrder : bool

    # Header Count, Reversed Order,  Date, Close, Open, High, Low, Volume
    def __init__(self, headerCount, reversedOrder, dateIndex, closeIndex, openIndex, highIndex, lowIndex, volumeIndex):
        super(GenericCSVProviderBuilder, self).__init__()
        self.headerCount = headerCount
        self.reversedOrder = reversedOrder
        self.dateIndex = dateIndex
        self.closeIndex = closeIndex
        self.openIndex = openIndex
        self.lowIndex = lowIndex
        self.highIndex = highIndex
        self.volumeIndex = volumeIndex

    def parseRow(self, index, startDate, row):
        pass

    def getEncoding(self):
        pass

    def getData(self, ticker, startDate):

        lstData = list()
        lstIndex = list()

        self.filepath = self.filepath + "/" + ticker + ".csv"

        with open(self.filepath, 'r', encoding=self.getEncoding()) as textfile:
            rows = list(csv.reader(textfile))
            
            if self.reversedOrder:
                i = len(rows)
                for row in reversed(rows):
                    if i>self.headerCount: 
                        self.parseRow(startDate, row, lstData, lstIndex)
                    i = i-1
            else:
                i = 0
                for row in rows:
                    if i>=self.headerCount: 
                        self.parseRow(startDate, row, lstData, lstIndex)
                    i = i+1
        

        return self.transformToPanda(lstData, lstIndex)

# Data Provider = 2
class InvestingCSVDataProvider(GenericCSVProviderBuilder):
    
    
    # Header Count, Reversed Order,  Date, Close, Open, High, Low, Volume
    def __init__(self):
        super(InvestingCSVDataProvider, self).__init__(1,True, 0, 1, 2, 3, 4, 5)

    def getEncoding(self):
        return "UTF-8"

    def parseRow(self, startDate, row, lstData, lstIndex):

        date_object = datetime.datetime.strptime(row[self.dateIndex], "%b %d, %Y")

        if date_object < startDate:
            return

        if row[self.volumeIndex][-1] == "M": 
            volume = float(row[self.volumeIndex][0:-1])*1000000
        elif row[self.volumeIndex][-1] == "K":
            volume = float(row[self.volumeIndex][0:-1])*1000
        elif row[self.volumeIndex][-1] == "-":
            volume=0
        else:
            volume = float(row[self.volumeIndex])

        lstData.append([float(row[self.openIndex]), 
                        float(row[self.highIndex]), 
                        float(row[self.lowIndex]), 
                        float(row[self.closeIndex]), 
                        float(row[self.closeIndex]), 
                        volume])
        lstIndex.append(date_object)

# Data Provider = 3
class ILCSVDataProvider(GenericCSVProviderBuilder):
    
    
    # Header Count, Reversed Order,  Date, Close, Open, High, Low, Volume
    def __init__(self):
        super(ILCSVDataProvider, self).__init__(1,True, 0, 1, 2, 3, 4, 5)

    def getEncoding(self):
        return "ANSI"

    def parseRow(self, startDate, row, lstData, lstIndex):

        date_object = datetime.datetime.strptime(row[self.dateIndex], "%d.%m.%Y")

        if date_object < startDate:
            return

        if row[self.volumeIndex][-1] == "M": 
            volume = float(row[self.volumeIndex][0:-1])*1000000
        elif row[self.volumeIndex][-1] == "K":
            volume = float(row[self.volumeIndex][0:-1])*1000
        elif row[self.volumeIndex][-1] == "-":
            volume=0
        else:
            volume = float(row[self.volumeIndex])

        lstData.append([float(row[self.openIndex]), 
                        float(row[self.highIndex]), 
                        float(row[self.lowIndex]), 
                        float(row[self.closeIndex]), 
                        float(row[self.closeIndex]), 
                        volume])
        lstIndex.append(date_object)

# Data Provider = 4
class Investing2DatesCSVDataProvider(GenericCSVProviderBuilder):
    
    
    # Header Count, Reversed Order,  Date, Close, Open, High, Low, Volume
    def __init__(self):
        super(Investing2DatesCSVDataProvider, self).__init__(1,False, 0, 2, 3, 4, 5, 6)

    def getEncoding(self):
        return "UTF-8"

    def parseRow(self, startDate, row, lstData, lstIndex):

        date_object = datetime.datetime.strptime(row[self.dateIndex], "%b %d, %Y")

        if date_object < startDate:
            return

        if row[self.volumeIndex][-1] == "M": 
            volume = float(row[self.volumeIndex][0:-1])*1000000
        elif row[self.volumeIndex][-1] == "K":
            volume = float(row[self.volumeIndex][0:-1])*1000
        elif row[self.volumeIndex][-1] == "-":
            volume=0
        else:
            volume = float(row[self.volumeIndex])

        lstData.append([float(row[self.openIndex]), 
                        float(row[self.highIndex]), 
                        float(row[self.lowIndex]), 
                        float(row[self.closeIndex]), 
                        float(row[self.closeIndex]), 
                        volume])
        lstIndex.append(date_object)

#https://stockinvest.us/
# Data Provider = 5
class StockInvestCSVDataProvider(GenericCSVProviderBuilder):
    
    
    # Header Count, Reversed Order,  Date, Close, Open, High, Low, Volume
    def __init__(self):
        super(StockInvestCSVDataProvider, self).__init__(1,True, 0, 4, 1, 2, 3, 5)

    def getEncoding(self):
        return "UTF-8"

    def parseRow(self, startDate, row, lstData, lstIndex):

        date_object = datetime.datetime.strptime(row[self.dateIndex], "%d/%m/%Y")

        if date_object < startDate:
            return

        volume = float(row[self.volumeIndex])

        lstData.append([float(row[self.openIndex][1:]), 
                        float(row[self.highIndex][1:]), 
                        float(row[self.lowIndex][1:]), 
                        float(row[self.closeIndex][1:]), 
                        float(row[self.closeIndex][1:]), 
                        volume])
        lstIndex.append(date_object)

class YahooFinancePricesBuilder:
    providers_types= {1: YahooDataProviderBuilder, 
                      2:InvestingCSVDataProvider,
                      3:ILCSVDataProvider,
                      4:Investing2DatesCSVDataProvider,
                      5:StockInvestCSVDataProvider}

    def GetFileLastDate(self, filePath):
        original_stdout = sys.stdout # Save a reference to the original standard output
        lastDate = None

        if os.path.exists(filePath):
            i=0
            with open(filePath, 'r+', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    i = i+1
                
                if i > 1:
                    lastDate = row[0][0:10]
        else:
            with open(filePath, 'w+') as f:
                sys.stdout = f # Change the standard output to the file we created.
                print('Datetime,Open,High,Low,Close,Adj Close,Volume')
        
        sys.stdout = original_stdout
        return lastDate

    def BuildFile(self, ticker, startDate, providers=[1], multiplier=1.0):

        filePath = 'C:/PythonScripts/Projects/BackTrader/Prices/' + ticker + '.csv'
        lastActiveDate = self.GetFileLastDate(filePath)
        if lastActiveDate != None: 
            startDate = datetime.datetime.strptime(lastActiveDate,'%Y-%m-%d') + datetime.timedelta(days = 1)

        original_startdate = startDate
        original_stdout = sys.stdout # Save a reference to the original standard output

        df_list = list()
        df_list.clear()

        low_multiplier = 0.95
        high_multiplier = 1.05
        if ticker.find(".TA") > -1:
            multiplier = multiplier * 0.01 / 3.1

        
        rowsperday = 3
        
        try:

            for provider in providers:
                lst = self.providers_types[provider]().getData(ticker, startDate)
                startDate = startDate if lst[0]['Open'].empty else (lst[0]['Open'].index[len(lst[0]['Open'])-1]) + datetime.timedelta(days = 1)
                df_list.append(lst)

            startDate = original_startdate
            dataIndex = 0

            with open(filePath, 'a') as f:
                sys.stdout = f # Change the standard output to the file we created.

                for dFrames in df_list:
                    for dataFrame in dFrames:
                
                        delta = 0 if dataFrame['Open'].empty else (dataFrame['Open'].index[0] - startDate).days
                        for day in range (0,delta):
                            startTime = startDate + datetime.timedelta(hours = 9) + datetime.timedelta(days = day)
                            self.printRow( dataFrame, 0, startTime, multiplier, low_multiplier, high_multiplier, rowsperday)

                        for dataIndex in range(0,len(dataFrame['Open'])):
                            startTime = dataFrame['Open'].index[dataIndex] + datetime.timedelta(hours = 9)
                            if startTime < startDate: 
                                continue
                            self.printRow( dataFrame, dataIndex, startTime, multiplier, low_multiplier, high_multiplier, rowsperday)
                
                        startDate = startDate if len(dataFrame['Open']) == 0 else startTime + datetime.timedelta(days = 1)

                # Fill the data for the last rows until now
                if not dataFrame.empty:
                    delta = (datetime.datetime.now() - startDate).days
                    for day in range (0,delta):
                        startTime = startDate + datetime.timedelta(days=day)
                        self.printRow( dataFrame, dataIndex, startTime, multiplier, low_multiplier, high_multiplier, rowsperday)

                sys.stdout = original_stdout
        except BaseException as err:
            sys.stdout = original_stdout
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error with: ", ticker)

    def printRow(self, dataFrame, dataIndex, startTime, multiplier, low_multiplier, high_multiplier, rowsperday):
        
        for minute in range(0,rowsperday):
            startTime = startTime + datetime.timedelta(minutes = 20)
            print("%s,%s,%s,%s,%s,%s,%s"%(startTime.strftime("%Y-%m-%d"), 
                                            round(dataFrame['Open'][dataIndex]*multiplier,4), 
                                            round(dataFrame['High'][dataIndex]*multiplier*high_multiplier,4),
                                            round(dataFrame['Low'][dataIndex]*multiplier*low_multiplier,4), 
                                            round(dataFrame['Close'][dataIndex]*multiplier,4), 
                                            round(dataFrame['Close'][dataIndex]*multiplier,4),
                                            round(dataFrame['Volume'][dataIndex],2)
                                            ))

if __name__ == '__main__':

    '''
    tickerStrings = ['DNA', 'ENTX', 'EDIT', 'CLGN', 'EYES', 'EXAS', 'MITC', 'MDWD', 'CHEK', 
				    'AQB','RCEL', 'NNOX','ENLV','ASML', 'ALCRB.PA', 'NXFR.TA', 'MTLF.TA', 'BMLK.TA', 
				    'NXGN.TA', 'PHGE.TA',  'ICCM.TA', 'CRTX', 'SPCE', 'SEDG', 'APLP.TA', 'AQUA.TA', 'PLX.TA', 'ENLT.TA', 'ECPA.TA', 'FVRR', 'SLGN.TA', 'UAL', 'SRNG', 'PHGE', 'BVXV',
                    'MMM','ATVI','GOOG','AMZN','AAPL','AVH.AX','BRK-B','BYND','CHKP','CTMX','EA','EQIX','FB','GE','GHDX','GILD','GSK','INTC','JUNO','KITE','LGND','MLNX',
                    'MU','NTGN','NFLX','ORBK','QCOM','RWLK','SGMO','TTWO','TSLA','TEVA','UPS','URGN','ENLV.TA','TEVA.TA','PSTI.TA']
    '''
    #tickerStrings = ['ICCM.TA']



    # For testing purposes only!
    YahooFinancePricesBuilder().BuildFile('DNA',datetime.datetime.strptime('2016-12-31', '%Y-%m-%d'),providers=[2,1])
    #YahooFinancePricesBuilder().BuildFile('XBI',datetime.datetime.strptime('2017-01-01', '%Y-%m-%d'))
    #YahooFinancePricesBuilder.GetFileLastDate('c:/prices/ICCM.TA.csv')