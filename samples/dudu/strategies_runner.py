from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import sys
import argparse
import datetime

from backtrader.analyzers.transactions import Transactions
from backtrader.functions import Or

import numpy as np

import backtrader as bt
from backtrader.analyzers import (AnnualReturn, DrawDown, TimeDrawDown, SharpeRatio, Returns, SQN, TimeReturn,
                                  TradeAnalyzer, annualreturn)
from backtrader.filters import CalendarDays

from analyzers import *
from transactionsLoader import *
from GetPrices import *
from backtrader.analyzers.sharpe import SharpeRatio_A
from strategies import *
from commissions import *
from strategies_plot import my_heatmap

def printResults(final_results_dict):

    headerKey                       = 'Parameter Name\t\t\t'
    underlineKey                    = '--------------\t\t\t'
    startWorthKey                   = 'Cash Worth\t\t\t'
    endWorthKey                     = 'End Worth\t\t\t'
    pnlKey                          = 'PNL\t\t\t\t'
    annualizedReturnsKey            = 'Annualised returns\t\t'
    annualizedVolatilityKey         = 'Annualised volatility\t\t'
    sharpeKey                       = 'Sharpe\t\t\t\t'
    drawDownKey                     = 'Draw Down\t\t\t'
    drawDownPeriodKey               = 'Draw Down Period (Days)\t\t'

    lines = {}
    lines[headerKey]                = ''
    lines[underlineKey]             = ''
    lines[startWorthKey]            = ''
    lines[endWorthKey]              = ''
    lines[pnlKey]                   = ''
    lines[annualizedReturnsKey]     = ''
    lines[annualizedVolatilityKey]  = ''
    lines[sharpeKey]                = ''
    lines[drawDownKey]              = ''
    lines[drawDownPeriodKey]        = ''

    zeroOnce = False
    for key in final_results_dict:
        lines[headerKey]                = lines[headerKey] + key.__name__ + '\t\t'
        lines[underlineKey]             = lines[underlineKey] + '-----------\t\t'
        lines[startWorthKey]            = lines[startWorthKey] + '%.2F\t\t'% (final_results_dict[key][0][0])
        lines[endWorthKey]              = lines[endWorthKey] + '%.2F\t\t'% (final_results_dict[key][0][1])
        lines[pnlKey]                   = lines[pnlKey] + '%.2F\t\t'% (final_results_dict[key][0][2])
        lines[annualizedReturnsKey]     = lines[annualizedReturnsKey] + '%.2F\t\t\t'% (final_results_dict[key][0][3])
        lines[annualizedVolatilityKey]  = lines[annualizedVolatilityKey] + '%.2F\t\t\t'% (final_results_dict[key][0][4])
        lines[sharpeKey]                = lines[sharpeKey] + '%.2F\t\t\t'% (final_results_dict[key][0][5])
        lines[drawDownKey]              = lines[drawDownKey] + '%.2F\t\t\t'% (final_results_dict[key][0][6])
        lines[drawDownPeriodKey]        = lines[drawDownPeriodKey] + '%.2F\t\t\t'% (final_results_dict[key][0][7])

        if not zeroOnce:
            for yearKey in (final_results_dict[key][0][8]):
                lines['Draw Down %s\t\t\t'% (yearKey)] = ''
                lines['Draw Down Period (Days) %s\t'% (yearKey)] = ''
            zeroOnce = True

        for yearKey in (final_results_dict[key][0][8]):
            lines['Draw Down %s\t\t\t'% (yearKey)] = lines['Draw Down %s\t\t\t'% (yearKey)] + '%.2F%%\t\t\t'% (final_results_dict[key][0][8][yearKey].max.drawdown)
            lines['Draw Down Period (Days) %s\t'% (yearKey)] = lines['Draw Down Period (Days) %s\t'% (yearKey)] + '%.2F\t\t\t'% (final_results_dict[key][0][8][yearKey].max.len/24)
        
    for key in lines:
        print(key+lines[key])

def loadSymbols(updatePrices, fromdate):

    
    yahooTickerStrings = ['CRTX', 'ALCRB.PA', 'CLGN', 'ENLV', 'PHGE', 'EDIT', 'MTLF.TA', 
                            'BMLK.TA', 'ICCM.TA', 'MDWD', 'EXAS', 'MITC', 'ENTX', 'DNA', 
                            'PHGE.TA', 'RCEL', 'NXFR.TA', 'AVH.AX', 'BYND', 'BVXV', 
                             'RWLK', 'SGMO', 'URGN', 'ENLV.TA', 'PSTI.TA',
                             'NXGN.TA']
    
    
    #yahooTickerStrings = ['CLGN', 'MTLF.TA']

    otherTickerStrings = []# 'SRNG', 'GHDX', 'JUNO', 'KITE','NTGN', FAKE1, FAKE2
    dataProviders = {'DNA' : [2,1] }


    symbolDataIndexes = {}
    i=0
    for ticker in yahooTickerStrings:
        transactionsLoader = TransactionsLoader()
        symbolDataIndexes[i] = {'ticker':ticker, 'transactions':transactionsLoader.Load(ticker)}
        if updatePrices:
            YahooFinancePricesBuilder().BuildFile(ticker, fromdate, dataProviders.get(ticker,[1]))
        i = i+1

    # Need to adjust the dates here to start at 1/1/2017
    for ticker in otherTickerStrings:
        symbolDataIndexes[i] = {'ticker':ticker, 'transactions':TransactionsLoader().Load(ticker)}
        i = i+1
    return symbolDataIndexes

def runstrategy():
    args = parse_args()

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    fencingpath = os.path.join(modpath, args.data + 'XBI' + '.csv')

    final_results_dict = {}
    strategies_list = [OldStrategy]
    #strategies_list = [OldStrategyWithETFFencing]

    symbolDataIndexes = loadSymbols(args.updatePrices, fromdate)

    for strat in strategies_list:
        
        cerebro = bt.Cerebro(optreturn=False)

        for index in symbolDataIndexes:
            datapath = os.path.join(modpath, args.data + symbolDataIndexes[index]['ticker'] + '.csv')
            data = bt.feeds.YahooFinanceCSVData(
                dataname=datapath,
                fromdate=fromdate,
                todate=todate,
            )

            data.addfilter(CalendarDays, fill_price=0, fill_vol=1000000)
            cerebro.adddata(data, name=symbolDataIndexes[index]['ticker'])

        fencingData = bt.feeds.YahooFinanceCSVData(
            dataname=fencingpath,
            fromdate=fromdate,
            todate=todate,
        )

        fencingData.addfilter(CalendarDays, fill_price=0, fill_vol=1000000)
        cerebro.adddata(fencingData, name='Fencing')
        cerebro.addstrategy(strat, symbol=args.symbol, priceSize=1, symbolsMapper=symbolDataIndexes)

        results_list = []

        cerebro.broker.set_coc(True)
        cerebro.broker.setcash(args.cash)
        #cerebro.addsizer(MaxRiskSizer)
        comminfo = PoalimCommission()
        cerebro.broker.addcommissioninfo(comminfo)

        tframes = dict(
            days=bt.TimeFrame.Days,
            weeks=bt.TimeFrame.Weeks,
            months=bt.TimeFrame.Months,
            years=bt.TimeFrame.Years)

        # Add the Analyzers
        #cerebro.addanalyzer(SQN)
        cerebro.addanalyzer(TimeReturn, _name='time_return', timeframe=tframes[args.tframe])
        cerebro.addanalyzer(TimeReturn, _name='time_return_fencing', data=fencingData, timeframe=tframes[args.tframe])
        cerebro.addanalyzer(SharpeRatio_A, timeframe=tframes[args.tframe], stddev_sample=True)
        cerebro.addanalyzer(Volatility)
        cerebro.addanalyzer(Transactions)
        cerebro.addanalyzer(TradeAnalyzer)
        cerebro.addanalyzer(DrawDownPerYear)

        cerebro.broker.set_fundmode(True)

        cerebro.addobserver(bt.observers.FundValue)
        cerebro.addobserver(bt.observers.FundShares)
        
        st0 = cerebro.run()
        
        my_dict = st0[0].analyzers.time_return.get_analysis()
        annual_returns = [v+1 for _, v in my_dict.items()]
        fdict = st0[0].analyzers.time_return_fencing.get_analysis()
        fencingreturns = [[v,fdict[v]] for v in fdict if fdict[v] <= -1 ]
        annualReturn = math.prod(annual_returns)
        
        cashWorth = st0[0].cash_addition + args.cash
        endWorth = round(st0[0].broker.get_value(), 2)
        PnL = round(endWorth - cashWorth, 2)
        transactionsList = list(st0[0].analyzers.transactions.get_analysis())
        years = (transactionsList[-1] - transactionsList[0]).days / 365.25

        compaund_annual_return = np.power(annualReturn, 1 / years)-1
        annualReturn = round(compaund_annual_return*100, 2)
        volatility = round(st0[0].analyzers.volatility.get_analysis()['volatility']*100,2)
        sharpe = round(st0[0].analyzers.sharperatio_a.get_analysis()['sharperatio'],2)
        drawDownPercentage = round(st0[0].analyzers.drawdownperyear.get_analysis()['max']['drawdown'],2)
        drawDownPeriod = round(st0[0].analyzers.drawdownperyear.get_analysis()['max']['len'] / 24,2)
        drawdownPerYear = st0[0].analyzers.drawdownperyear.get_analysis()['drawDownsPerYear']


        results_list.append([
            cashWorth,
            endWorth,
            PnL,
            annualReturn,
            volatility,
            sharpe,
            drawDownPercentage,
            drawDownPeriod,
            drawdownPerYear
        ])
        final_results_dict[strat] = results_list

        trackedorders=[]
        nonexecuted_transactions = {}
        for tickerIndex in st0[0].pastTransactions:
            transData = st0[0].pastTransactions[tickerIndex]
            for transaction in transData['transactions'][0:-1]:
                res =  [order for order in st0[0].broker.orders 
                        if transData['data'] is order.params.data and 
                        not order.executed.dt is None and
                        (int(order.executed.dt) == bt.date2num(transaction.transactionDate) or 
                        int(order.executed.dt) == bt.date2num(transaction.transactionDate + datetime.timedelta(days = 1))) and
                        abs(order.executed.size) == transaction.amount and 
                        not order in trackedorders]
                if len(res) > 0:
                    trackedorders.append(res[0])
                else:
                    lst = nonexecuted_transactions.setdefault(transData['ticker'], [])
                    lst.append(transaction)

                #price,size

        for order in st0[0].broker.orders:
             metaData = [st0[0].pastTransactions[transdata] for transdata in st0[0].pastTransactions if st0[0].pastTransactions[transdata]['data'] is order.params.data][0]


    # Average results for the different data feeds
    #arr = np.array(final_results_dict)
    #final_results_dict = [[int(val) if val.is_integer() else round(val, 2) for val in i] for i in arr.mean(0)]

    printResults(final_results_dict)
    printValidationResults(nonexecuted_transactions)

    if args.plot:
            cerebro.plot()
  
def printValidationResults(results):
    for ticker in results:
        for transaction in results[ticker]:
            print("%s. Date: %s, Amount:%.4F"%(ticker, transaction.transactionDate, transaction.amount))

def parse_args():
    parser = argparse.ArgumentParser(description='TimeReturn')
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    parser.add_argument('--symbol', '-s',
                        default='ICCM.TA',
                        help='specific symbol to add to the system')

    parser.add_argument('--data', '-d',
                        default=os.path.join(modpath,'../../prices/'),
                        help='data to add to the system')


    parser.add_argument('--fromdate', '-f', default='2016-12-31',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t', default='2021-12-19',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--fast_period', default=13, type=int,
                        help='Period to apply to the Exponential Moving Average')

    parser.add_argument('--slow_period', default=48, type=int,
                        help='Period to apply to the Exponential Moving Average')

    parser.add_argument('--longonly', '-lo', action='store_true',
                        help='Do only long operations')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--tframe', default='years', required=False,
                       choices=['days', 'weeks', 'months', 'years'],
                       help='TimeFrame for the returns/Sharpe calculations')

    group.add_argument('--legacyannual', action='store_true',
                       help='Use legacy annual return analyzer')

    #parser.add_argument('--cash', default=100000 / 3.1, type=int,
    #                    help='Starting Cash')

    parser.add_argument('--cash', default=1000, type=int,
                        help='Starting Cash')


    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--updatePrices', '-u', action='store_false',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='Plot using numfigs figures')

    parser.add_argument('--optimize', '-opt', default=1,
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()