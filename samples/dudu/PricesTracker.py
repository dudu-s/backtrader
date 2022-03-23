from time import strftime, strptime
from numpy import NaN, unicode_
from pandas.core.base import NoNewAttributesMixin
import yfinance as yf
import sys
import os
import numpy as np
import csv
import math
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d




class CacheData:
    path = 'cache.csv'
    data = dict()
    

    def add(self, date, ticker, price):
        self.data[date.strftime("%Y-%m-%d")+"@"+ticker] = price

    def get(self, date, ticker):
        return self.data.get(date.strftime("%Y-%m-%d")+"@"+ticker, None)

    def load(self, startdate):

        if not os.path.exists(self.path):
            self.write()

        with open(self.path, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                date   = row[0]
                if datetime.datetime.strptime(date,'%Y-%m-%d') >= startdate:
                    ticker   = row[1]
                    price         = float(row[2])
                    
                    self.data[date+"@"+ticker] = price
                    
    def write(self):
        original_stdout = sys.stdout # Save a reference to the original standard output

        # Save the files

        sortedData = dict(sorted(self.data.items(), key=lambda item: item[0].split("@")[0]))
            
        

        with open(self.path, 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.

            for priceInfo in sortedData:
                x = priceInfo.split("@")
                print("%s,%s,%s"%(x[0],x[1],self.data[priceInfo]))

        sys.stdout = original_stdout

    def calculateDailyReturn(self, tickers, enddate):
        sortedData = dict(sorted([it for it in self.data.items()  if it[0].split("@")[1] in tickers], key=lambda item: item[0].split("@")[0]))
        x = []
        y = []
        prices1 = {}
        prices2 = {}
        weight = 1 / len(tickers)
        previousdate = datetime.datetime.now()
        

        for itemInfo in sortedData:
            item = itemInfo.split("@")
            currentdate = datetime.datetime.strptime(item[0], '%Y-%m-%d')
            #if datetime.datetime.strptime(item[0], "%Y-%m-%d") >= enddate:
             #   break
            
            if (previousdate !=  currentdate):
                if len(prices1) > 0:

                    if len(prices2) > 0:
                        x.append(previousdate)
                        y.append(round(sum([(prices1[p1] / prices2[p1] - 1) * weight for p1 in prices1 if p1 in prices2]) * 100,5))
                        
                        delta = (currentdate-previousdate).days
                        for i in range(delta-1):
                            x.append(previousdate + datetime.timedelta(days=i+1))
                            y.append(NaN)


                    prices2 = prices1
                    prices1 = {}
                
            previousdate = currentdate
            prices1[item[1]] = sortedData[itemInfo]

        if len(prices2) > 0: 
            x.append(previousdate)
            y.append(round(sum([(prices1[p1] / prices2[p1] - 1) * weight for p1 in prices1 if p1 in prices2]) * 100,5))

        return [x,y]




class YahooFinancePricesTracker:
    tickers = []

    def __init__(self, startdate):
        self.cacheddata = CacheData()
        self.cacheddata.load(startdate)

    def loadPeriodData(self, ticker, startDate, endDate):
        delta = (endDate - startDate).days + 1
        startQuery = None
        endQuery = None
        
        #1st condition - no  data at all
        for day in range(delta):
            date = startDate + datetime.timedelta(days = day)
            
            if self.cacheddata.get(date, ticker) is None:
                if endQuery is None:
                    endQuery = date

            if not self.cacheddata.get(date, ticker) is None:
                if startQuery is None:
                    self.downloadAndCache(ticker, startDate, date)
                    startQuery = startDate
                endQuery = None
                
        if not endQuery is None:
            self.downloadAndCache(ticker, endQuery, endDate)
        
        
    
    def downloadAndCache(self, ticker, startDate, endDate):
        if startDate == endDate:
            return
        
        data  = self.downloadData(ticker, startDate, endDate)
            
        for i in range(len(data.Close)):
            price = round(data.Close[i],2)
            date = data.Close.index[i]
            self.cacheddata.add(date, ticker, price)

    def getLastValidPrice(self, ticker, startDate):
        price = self.getSingleDayPrice(ticker, startDate)
        maxdays = 5
        i = 0
        while (price is None and i < maxdays):
            price = self.getSingleDayPrice(ticker, startDate - datetime.timedelta(days=i))
            i = i + 1

        return price

    def getSingleDayPrice(self, ticker, startDate):
        price = None
        price = self.cacheddata.get(startDate, ticker)

        if price is None:
            data = self.downloadData(ticker, startDate, startDate+datetime.timedelta(days=1))
            if (len(data.Close > 0)):
                price = round(data.Close[-1],2)
    
        return price

    def downloadData(self, ticker, startDate, enddate):
        enddate = enddate + datetime.timedelta(days=1)
        orig_stdout = sys.stdout
        sys.stdout=open('log.txt','a')
        data = yf.download(ticker, group_by="Ticker", start=startDate, end=enddate, interval="1d")
        sys.stdout.close()
        sys.stdout=orig_stdout 
        return data


    def PrintResults(self, tickers, startDate, enddate, detailed=False, plot=True):
        self.tickers = tickers
        #startDate = enddate - datetime.timedelta(days = 3)

        df_list = list()
        df_list.clear()
        lines = []

        weight = 1/len(tickers)
        average = 0


        try:

            for tickerInfo in tickers:
                ticker = tickerInfo['ticker']

                self.loadPeriodData(ticker, startDate, enddate)
                closePrice = self.getLastValidPrice(ticker, enddate-datetime.timedelta(days=1))
                refPrice = self.getSingleDayPrice(ticker, tickerInfo['StartDate'])
                
                percentage = round((closePrice / refPrice - 1) * 100,3) 
                days = (enddate - tickerInfo['StartDate']).days
                average = weight * percentage + average
                
                if len(ticker) < 8:
                    ticker = ticker+"\t"

                lines.append ("%s\t%s\t%s\t\t%s\t\t%s%%\t\t%s"%(ticker,
                                            closePrice,
                                            round(refPrice,2),
                                            round(tickerInfo['DestPrice'],2),
                                            percentage,
                                            days))
            if detailed:
                print ("Ticker\t\tPrice\tStart Price\tDest Price\tPercentage\tDays")
                for line in lines:
                    print(line)
            
            print ('')
            print (' ------------------ ')
            print ('Average: %s' %(round(average,2)) )

            self.cacheddata.write()
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error with: ", ticker)

def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]

def interpolate(data):
    y = np.array(data)
    nans, x= nan_helper(y)
    y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    return y

def plotPricesTracker(yfs, enddate):
    i = 0
    data = []
    yaxis = []
    products = []
    fig, (ax1, ax2) = plt.subplots(2)

    fig.suptitle('Vertically stacked subplots')
       # yfs = [{'yf':yf1, 'Text':'Excellence'},
    
    
    for p in yfs:
        data.append(p['yf'].cacheddata.calculateDailyReturn([ticker['ticker'] for ticker in p['yf'].tickers], enddate))
        ax1.plot(data[-1][0], interpolate(data[-1][1]), label=p['Text'])
        ax1.legend()
        ax1.set_title('Daily Returns')
        products.append(1)
        yaxis.append([])
    
    
    dataIndex = 0
    for dataIndex in range(len(yfs)):
        for i in range(len(data[dataIndex][1])):
            if math.isnan(data[dataIndex][1][i]) == False:
                products[dataIndex] = products[dataIndex] * (data[dataIndex][1][i] / 100 + 1)
            yaxis[dataIndex].append(round((products[dataIndex] - 1) * 100,5))


    dataIndex = 0
    for dataIndex in range(len(yfs)):
        ax2.plot(data[dataIndex][0], yaxis[dataIndex], label=yfs[dataIndex]['Text'])
        ax2.legend()
        ax2.set_title('Period Returns')
        fig.tight_layout(pad=1.0)

    
    plt.show()

if __name__ == '__main__':

    
    
    tickers1 = [{'ticker':'TSM', 'DestPrice':160, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'QCom', 'DestPrice':250, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'MSFT', 'DestPrice':365, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'GOOG', 'DestPrice':3500, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'AMZN', 'DestPrice':4000, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'V', 'DestPrice':302, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'UPS', 'DestPrice':272, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'SPY', 'DestPrice':520, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               ]

   
    tickers2 = [{'ticker':'PHGE', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}, 
               {'ticker':'MITC', 'DestPrice':6.54, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'DNA', 'DestPrice':12.34, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'ENTX', 'DestPrice':3.82, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'EDIT', 'DestPrice':36.1, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'CLGN', 'DestPrice':17.11, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'EYES', 'DestPrice':2.41, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'EXAS', 'DestPrice':97.61, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'MDWD', 'DestPrice':3.2, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'CHEK', 'DestPrice':0.81, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'RCEL', 'DestPrice':17.81, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'NNOX', 'DestPrice':24.94, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'ENLV', 'DestPrice':8.86, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'ASML', 'DestPrice':750, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'WILK.TA', 'DestPrice':309.41, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'ALCRB.PA', 'DestPrice':38.9, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'NXFR.TA', 'DestPrice':758.28, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'MTLF.TA', 'DestPrice':1076.38, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'NXGN.TA', 'DestPrice':288.6, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'ICCM.TA', 'DestPrice':1561.99, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               ]

    tickers3 = [{'ticker':'VLO', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}, 
               {'ticker':'TTE', 'DestPrice':6.54, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
               {'ticker':'AMCR', 'DestPrice':6.54, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}]

    tickers4 = [{'ticker':'TQQQ', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}]

    tickers5 = [{'ticker':'GLNG', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-14', '%Y-%m-%d')}]

    #lst = [ticker['ticker'] for ticker in tickers2]
    #YahooFinancePricesTracker().getPeriodData('ASML', datetime.datetime.strptime('2022-03-01', '%Y-%m-%d'), datetime.datetime.strptime('2022-03-02', '%Y-%m-%d'))

    #tickers1 = [{'ticker':'WILK.TA', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}]

    enddate = datetime.datetime.now() - datetime.timedelta(days = 1)
    startdate = datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')
    if enddate.weekday() >= 5:
        enddate = enddate - datetime.timedelta(days = enddate.weekday() - 4)

    
    yfs = [{'yf':YahooFinancePricesTracker(startdate), 'Text':'Excellence'},
           {'yf':YahooFinancePricesTracker(startdate), 'Text':'Healthcare'},
           {'yf':YahooFinancePricesTracker(startdate), 'Text':'TipRanks'},
           {'yf':YahooFinancePricesTracker(startdate), 'Text':'Stuff'},
           {'yf':YahooFinancePricesTracker(tickers5[0]['StartDate']), 'Text':'TipRanks2'}]

    yfs[0]['yf'].PrintResults(tickers1, startdate, enddate, False)
    yfs[1]['yf'].PrintResults(tickers2, startdate, enddate, False)
    yfs[2]['yf'].PrintResults(tickers3, startdate, enddate, False)
    yfs[3]['yf'].PrintResults(tickers4, startdate, enddate, False)
    yfs[4]['yf'].PrintResults(tickers5, tickers5[0]['StartDate'], enddate, False)


    plotPricesTracker(yfs, enddate)

    