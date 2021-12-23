from time import strptime
import yfinance as yf
import sys
import datetime
import csv
import os.path


class YahooFinancePricesBuilder:

    def GetFileLastDate(self, filePath):
        original_stdout = sys.stdout # Save a reference to the original standard output
        lastDate = None

        if os.path.exists(filePath):
            i=0
            with open(filePath, 'r+', newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in spamreader:
                    i = i+1
                lastDate = row[0][0:10]
        else:
            with open(filePath, 'w+') as f:
                sys.stdout = f # Change the standard output to the file we created.
                print('Datetime,Open,High,Low,Close,Adj Close,Volume')
        
        sys.stdout = original_stdout
        return lastDate

    def BuildFile(self, ticker, startDate, multiplier=1.0):

        filePath = 'C:/PythonScripts/Projects/BackTrader/datas/' + ticker + '.csv'
        lastActiveDate = self.GetFileLastDate(filePath)
        if lastActiveDate != None: 
            startDate = datetime.datetime.strptime(lastActiveDate,'%Y-%m-%d') + datetime.timedelta(days = 1)


        original_stdout = sys.stdout # Save a reference to the original standard output

        df_list = list()
        df_list.clear()

        if ticker.find(".TA") > -1:
            multiplier = multiplier * 0.01
    
        try:

            data = yf.download(ticker, group_by="Ticker", start=startDate, end=datetime.datetime.now().strftime("%Y-%m-%d"), interval="1d")
            df_list.append(data)
            dataIndex = 0

            with open(filePath, 'a') as f:
                sys.stdout = f # Change the standard output to the file we created.

                for dataFrame in df_list:
                
                    for dataIndex in range(0,len(dataFrame['Open'])-1):
                        startTime = dataFrame['Open'].index[dataIndex] + datetime.timedelta(hours = 9)
                        for minute in range(1,25):
                            startTime = startTime + datetime.timedelta(minutes = 20)
                            print("%s,%s,%s,%s,%s,%s,%s"%(startTime, 
                                                            round(dataFrame['Open'][dataIndex]*multiplier,2), 
                                                            round(dataFrame['High'][dataIndex]*multiplier,2),
                                                            round(dataFrame['Low'][dataIndex]*multiplier,2), 
                                                            round(dataFrame['Close'][dataIndex]*multiplier,2), 
                                                            round(dataFrame['Close'][dataIndex]*multiplier,2),
                                                            round(dataFrame['Volume'][dataIndex],2)
                                                            ))
                
                sys.stdout = original_stdout
        except:
            sys.stdout = original_stdout
            print("Error with: ", ticker)


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
    YahooFinancePricesBuilder().BuildFile('XBI',datetime.datetime.strptime('2016-01-01', '%Y-%m-%d'))
    #YahooFinancePricesBuilder.GetFileLastDate('c:/prices/ICCM.TA.csv')