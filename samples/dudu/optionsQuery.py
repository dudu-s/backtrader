import requests
import sys
import csv
import os
import datetime
import time

# ORATS:
# https://docs.orats.io/data-explorer/index.html

def queryOptions(tickerStrings, fromdate, todate):
    baseurl = 'https://api.orats.io/datav2/hist/strikes.json'
    token='?token=75b991b4-745f-41d1-86fc-96a9e4a47d0f'
    tickers='&ticker=AAPL,IBM,ICCM.TA'
    tradedates='&tradeDate=2017-08-28'
    dte='&dte=0,365'
    fieldsStr='ticker,tradeDate,expirDate,dte,strike,stockPrice,callVolume,callOpenInterest,callBidSize,callAskSize,putVolume,putOpenInterest,putBidSize,putAskSize,callBidPrice,callValue,callAskPrice,putBidPrice,putValue,putAskPrice,callBidIv,callMidIv,callAskIv,smvVol,putBidIv,putMidIv,putAskIv,residualRate,delta,gamma,theta,vega,rho,phi,driftlessTheta,extSmvVol,extCallValue,extPutValue,spotPrice,updatedAt'
    fields='&fields='+fieldsStr
    path = 'C:/PythonScripts/Projects/BackTrader/OptionsPrices/'

    #"https://api.orats.io/datav2/hist/strikes?token=your-secret-token&ticker=AAPL&tradeDate=2017-08-28"

    # Find last active date
    lastActiveDate = GetFileLastDate(path, tickerStrings, fieldsStr)
    if lastActiveDate != None: 
        fromdate = (getdate(lastActiveDate) + datetime.timedelta(days = 1)).date()

    delta = (todate - fromdate).days

    tickersData={}
    for day in range(0,delta+1):
    
        # Build the trade date
        date = fromdate + datetime.timedelta(days = day)
        if date.weekday() >= 5:
            continue

        tradedates = '&tradeDate='+ date.strftime('%Y-%m-%d')

        i = 0
        j=0
        # Build the tickers string
        #tickers = '&ticker='
        tickersarr = []
        tickersarr.append('&ticker=')

        for ticker in tickerStrings:
            if i==10:
                tickersarr[j] = tickersarr[j][:-1]
                i=0
                j=j+1
                tickersarr.append('&ticker=')
            tickersarr[j] = tickersarr[j] + ticker + ','
            i = i+1

        tickersarr[j] = tickersarr[j][:-1]
    
        for tickers in tickersarr:
            try:
                # Get the data from the API
                url = baseurl + token + tickers + tradedates + dte + fields
                resp = requests.get(url=url)
                data = resp.json() # Check the JSON Response Content documentation below
                if resp.status_code != 200:
                   continue
                for line in data['data']:
                    tickersData[line['ticker']] = tickersData.get(line['ticker'], [])
        
                    lineStr = ""
                    for field in fieldsStr.split(","):
                        lineStr=lineStr+str(line[field])+','
                    tickersData[line['ticker']].append(lineStr[:-1])
        
            except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}")
                print("Error with: ", date.strftime('%Y-%m-%d'))

                # Remove all the current date lines
                for ticker in tickersData:
                    while(tickersData[ticker][len(tickersData[ticker])-1][5:15] == date.strftime('%Y-%m-%d')):
                        tickersData[ticker].pop()
            
                saveToFiles(tickersData, path)
                removeEmptyFiles(path, fieldsStr)
                raise
        
            print ('Saving %s'%(date.strftime('%Y-%m-%d')))

    saveToFiles(tickersData, path)
    removeEmptyFiles(path, fieldsStr)

def GetFileLastDate(path, tickerStrings, fieldsStr):
        original_stdout = sys.stdout # Save a reference to the original standard output
        lastDate = None

        for ticker in tickerStrings:
            filePath = path+ticker+'.csv'
            if os.path.exists(filePath):
                i=0
                with open(filePath, 'r+', newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in spamreader:
                        i = i+1
                
                    if i > 1:
                        lastDate = row[1] if lastDate is None or getdate(row[1]) > getdate(lastDate) else lastDate
            else:
                with open(filePath, 'w+') as f:
                    sys.stdout = f # Change the standard output to the file we created.
                    print(fieldsStr)
        
        sys.stdout = original_stdout
        return lastDate

def saveToFiles(tickersData, path):
    original_stdout = sys.stdout # Save a reference to the original standard output

    # Save the files
    for tickerData in tickersData:

        with open(path+tickerData+'.csv', 'a') as f:
            sys.stdout = f # Change the standard output to the file we created.

            for lineStr in tickersData[tickerData]:
                print(lineStr)

    sys.stdout = original_stdout

def removeEmptyFiles(path, fieldsStr):
    expectedSize = len(fieldsStr)+5
    # Remove the empty files
    for ticker in tickerStrings:
        filePath = path+ticker+'.csv'
        if os.path.exists(filePath) and os.path.getsize(filePath) < expectedSize:
            os.remove(filePath)


def getdate(date):
        try:
            datetoreturn = datetime.datetime.strptime(date,'%Y-%m-%d')
        except:
                datetoreturn = datetime.datetime.strptime(date,'%d/%m/%Y')
        return datetoreturn

def runFunc(tickerStrings, fromdate, todate, iteration=0):
    try:
        queryOptions(tickerStrings, fromdate, todate)
    except:
        if iteration < 5:
            time.sleep(30)
            runFunc(tickerStrings, fromdate, todate, iteration+1)

if __name__ == '__main__':

    tickerStrings = ['ALCRB.PA', 'CRTX', 'CLGN', 'ENLV', 'PHGE', 'EDIT', 'MTLF.TA', 
                                'BMLK.TA', 'ICCM.TA', 'DNA', 'MDWD', 'EXAS', 'MITC', 'ENTX',  
                                'PHGE.TA', 'RCEL', 'NXFR.TA', 'AVH.AX', 'BYND', 'BVXV', 
                                 'RWLK', 'SGMO', 'URGN', 'ENLV.TA', 'PSTI.TA','NXGN.TA',
                                 'MITC.TA', 'GHDX', 'NTGN','JUNO']

    
    #tickerStrings = ['DNA']
    
    '''
    print('Starting 2017')
    fromdate=datetime.date(2017,1,1)
    todate=datetime.date(2017,12,31)
    try:
        queryOptions(tickerStrings, fromdate, todate)
    except:
        time.sleep(5)
        queryOptions(tickerStrings, fromdate, todate)
    
    print('Finished 2017')
    '''
    print('Starting 2017')
    runFunc(tickerStrings, datetime.date(2017,1,1), datetime.date(2017,12,31))
    print('Finished 2017')

    print('Starting 2018')
    runFunc(tickerStrings, datetime.date(2018,1,1), datetime.date(2018,12,31))
    print('Finished 2018')
    
    print('Starting 2019')
    runFunc(tickerStrings, datetime.date(2019,1,1), datetime.date(2019,12,31))
    print('Finished 2019')

    print('Starting 2020')
    runFunc(tickerStrings, datetime.date(2020,1,1), datetime.date(2020,12,31))
    print('Finished 2020')

    print('Starting 2021')
    runFunc(tickerStrings, datetime.date(2021,1,1), datetime.date(2021,12,31))
    print('Finished 2021')

    print('Starting 2022')
    runFunc(tickerStrings, datetime.date(2022,1,1), datetime.date(2022,1,22))
    print('Finished 2022')
    name = 5
