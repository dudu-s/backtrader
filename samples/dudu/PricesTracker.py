from time import strftime, strptime
from numpy import unicode_
import yfinance as yf
import sys
import os
import datetime
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
    def getData(self, ticker, startDate,exactday=False):

        orig_stdout = sys.stdout
        sys.stdout=open('log.txt','w')

        df_list = list()
        df_list.clear()

        if exactday:
            enddate = startDate + datetime.timedelta(days=1)
        else:
            enddate = datetime.datetime.now()
        data = yf.download(ticker, group_by="Ticker", start=startDate.strftime("%Y-%m-%d"), end=enddate.strftime("%Y-%m-%d"), interval="1d")

        df_list.append(data)

        sys.stdout.close()
        sys.stdout=orig_stdout 

        return df_list



class YahooFinancePricesTracker:
    providers_types= {1: YahooDataProviderBuilder}


    def PrintResults(self, tickers, detailed=False):
        providers=[1]
        startDate = datetime.datetime.now() - datetime.timedelta(days = 3)

        df_list = list()
        df_list.clear()
        lines = []

        weight = 1/len(tickers)
        average = 0


        try:

            for tickerInfo in tickers:
                ticker = tickerInfo['ticker']


                for provider in providers:
                    lst = self.providers_types[provider]().getData(ticker, startDate)
                    df_list.append(lst)
                dataIndex = 0

                
                dataFrame = df_list[-1][-1]
                dataIndex = max(dataFrame['Open'].index)
                closePrice = round(dataFrame['Close'][dataIndex],2)
                
                for provider in providers:
                    lst = self.providers_types[provider]().getData(ticker, tickerInfo['StartDate'], True)
                    df_list.append(lst)
                dataFrame = df_list[-1][-1]
                dataIndex = max(dataFrame['Open'].index)
                refPrice = round(dataFrame['Close'][dataIndex],2)
                
                
                percentage = round((closePrice / refPrice - 1) * 100,3) 
                days = (datetime.datetime.now() - tickerInfo['StartDate']).days
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

                
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error with: ", ticker)

    

if __name__ == '__main__':

    
    
    tickers1 = [{'ticker':'MSFT', 'DestPrice':350, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}, 
               {'ticker':'TSM', 'DestPrice':160, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')},
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

    #tickers2 = [{'ticker':'WILK.TA', 'DestPrice':2.08, 'StartDate':datetime.datetime.strptime('2022-03-01', '%Y-%m-%d')}]

    # For testing purposes only!
    YahooFinancePricesTracker().PrintResults(tickers1, False)
    YahooFinancePricesTracker().PrintResults(tickers2, False)

    