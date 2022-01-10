from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import sys
import time
import argparse
import datetime
import concurrent.futures


from backtrader.analyzers.transactions import Transactions
from backtrader.functions import Or
from backtrader.observers import benchmark
from backtrader.observers.buysell import BuySell
from backtrader.observers.trades import Trades

import numpy as np

import backtrader as bt
from backtrader.analyzers import (AnnualReturn, DrawDown, TimeDrawDown, SharpeRatio, Returns, SQN, TimeReturn,
                                  TradeAnalyzer, annualreturn)
from backtrader.filters import CalendarDays

from observers import *
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
            for yearKey in sorted(final_results_dict[key][0][8].keys(), reverse=True):
                lines['Return %s\t\t\t'% (yearKey)] = ''
                lines['Draw Down %s\t\t\t'% (yearKey)] = ''
                lines['Draw Down Period (Days) %s\t'% (yearKey)] = ''
            zeroOnce = True

        i = 0
        size = len(final_results_dict[key][0][8].keys())
        for yearKey in sorted(final_results_dict[key][0][8].keys(), reverse=True):
            i = i + 1
            lines['Return %s\t\t\t'% (yearKey)] = lines['Return %s\t\t\t'% (yearKey)] + '%.2F%%\t\t\t'% ((final_results_dict[key][0][9][size - i] - 1)*100)
            lines['Draw Down %s\t\t\t'% (yearKey)] = lines['Draw Down %s\t\t\t'% (yearKey)] + '%.2F%%\t\t\t'% (final_results_dict[key][0][8][yearKey].max.drawdown)
            lines['Draw Down Period (Days) %s\t'% (yearKey)] = lines['Draw Down Period (Days) %s\t'% (yearKey)] + '%.2F\t\t\t'% (final_results_dict[key][0][8][yearKey].max.len/24)
    for key in lines:
        print(key+lines[key])

def loadSymbols(updatePrices, fromdate):

    
    tickerStrings = ['ALCRB.PA', 'CRTX', 'CLGN', 'ENLV', 'PHGE', 'EDIT', 'MTLF.TA', 
                            'BMLK.TA', 'ICCM.TA', 'MDWD', 'EXAS', 'MITC', 'ENTX', 'DNA', 
                            'PHGE.TA', 'RCEL', 'NXFR.TA', 'AVH.AX', 'BYND', 'BVXV', 
                             'RWLK', 'SGMO', 'URGN', 'ENLV.TA', 'PSTI.TA','NXGN.TA',
                             'MITC.TA', 'GHDX', 'NTGN','JUNO']
    
    
    #tickerStrings = ['ICCM.TA','EDIT']#,'CLGN', 'MTLF.TA']

    
    dataProviders = {'DNA' : [2,1],
                     'MITC.TA' : [3],
                     'GHDX' : [4],
                     'NTGN' : [2],
                     'JUNO':[5]}


    symbolDataIndexes = []
    i=0
    for ticker in tickerStrings:
        symbolDataIndexes.append([ticker, TransactionsLoader().Load(ticker)])
        if updatePrices:
            YahooFinancePricesBuilder().BuildFile(ticker, fromdate, dataProviders.get(ticker,[1]))
        i = i+1
    
    return symbolDataIndexes

def addData(cerebro, args, symbolDatas):
    
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    fencingpath = os.path.join(modpath, args.data + 'XBI' + '.csv')
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    for index in symbolDatas:
        datapath = os.path.join(modpath, args.data + index[0] + '.csv')
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=fromdate,
            todate=todate,
                
        )

        data.addfilter(CalendarDays, fill_price=0, fill_vol=1000000)
        data.plotinfo.plot = False
        cerebro.adddata(data, name=index[0])

    # Add fencing Data
    fencingData = bt.feeds.YahooFinanceCSVData(
        dataname=fencingpath,
        fromdate=fromdate,
        todate=todate,
    )

    fencingData.addfilter(CalendarDays, fill_price=0, fill_vol=1000000)
    cerebro.adddata(fencingData, name='Fencing')

def setCerebroParameters(cerebro, args):
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
    cerebro.addanalyzer(SharpeRatio_A, timeframe=tframes[args.tframe], stddev_sample=True)
    cerebro.addanalyzer(Volatility)
    cerebro.addanalyzer(Transactions)
    cerebro.addanalyzer(TradeAnalyzer)
    cerebro.addanalyzer(DrawDownPerYear)

    cerebro.broker.set_fundmode(True)

def addObservers(cerebro):
    cerebro.addobserver(CashObserver)
    cerebro.addobserver(FundObserver)
    cerebro.addobserver(bt.observers.TimeReturn)
    cerebro.addobserver(Trades)
    cerebro.addobserver(bt.observers.DrawDown)

def runstrategy():
    args = parse_args()
    optimize = False
    
    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')

    final_results_dict = {}


    if optimize:
        # --------  Optimized mode ----------
        symbolDataIndexes = [loadSymbols(args.updatePrices, fromdate)]
        strategies_dict =   {
                           #1:{'strategy':OldStrategy, 'kwargs':{'number_of_days' : [2,20,100], 'keep_cash_percentage':[0.1,0.2,0.3], 'symbolsMapper':symbolDataIndexes}},
                           2:{'strategy':OldStrategyWithTakeProfit, 'kwargs':{'number_of_days' : 2, 'keep_cash_percentage':0, 'symbolsMapper':symbolDataIndexes, 'take_profit_percentage' : [0.8,0.9,1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0]}}
                           #1:{'strategy':OldStrategy, 'kwargs':{'number_of_days' : 2, 'keep_cash_percentage':0.1, 'symbolsMapper':symbolDataIndexes, 'detailedLog':True}},
                           #2:{'strategy':OldStrategyWithETFFencing,'kwargs':{'detailedLog':True}}
                        }

        for stratKey in strategies_dict:
        
            cerebro = bt.Cerebro(optreturn=True, stdstats=False)
            stkwargs = strategies_dict[stratKey]['kwargs']

            addData(cerebro, args, symbolDataIndexes[0])
            cerebro.optstrategy(strategies_dict[stratKey]['strategy'], **stkwargs)
            setCerebroParameters(cerebro, args)

            now = datetime.datetime.now()
            stResults = cerebro.run()
            print("Elapsed Time: %d"%((datetime.datetime.now() - now).seconds))
            for st in stResults:
                results = getAnalysisResults(st[0], args)
                print("Optimize %.2F Cash, # Days %d:  Return:%.2F, STD: %.2F, Sharpe: %.2F"%(st[0].p.keep_cash_percentage, st[0].p.number_of_days, results[3], results[4], results[5]))
    else:
        
        # --------  Non optimized mode ----------
        symbolDataIndexes = loadSymbols(args.updatePrices, fromdate)
        strategies_dict =   {
                           1:{'strategy':OldStrategy, 'kwargs':{'number_of_days' : 2, 'keep_cash_percentage':0, 'symbolsMapper':symbolDataIndexes, 'detailedLog':True}},
                           2:{'strategy':OldStrategyWithTakeProfit, 'kwargs':{'number_of_days' : 2, 'keep_cash_percentage':0, 'symbolsMapper':symbolDataIndexes, 'detailedLog':True, 'take_profit_percentage' : 1.5}}
                           #2:{'strategy':OldStrategyWithETFFencing,'kwargs':{'detailedLog':True}}
                        }
        
        processes = []

        start = time.perf_counter()
        parallel = True

        if parallel:
            
            with concurrent.futures.ProcessPoolExecutor() as executor:

                for stratKey in strategies_dict:
                    strategies_dict[stratKey]['kwargs']['detailedLog'] = False
                    process1 = executor.submit(parallel_strat, args, stratKey, strategies_dict, symbolDataIndexes)
                    processes.append(process1)
                    
                    i = 0
                for stratKey in strategies_dict:
                    results = processes[i].result()
                    final_results_dict[strategies_dict[stratKey]['strategy']] = results[0]
                    nonexecuted_transactions = results[1]

                    i = i + 1

            end = time.perf_counter()       
            print(f'Finished in {round(end-start, 2)} second(s)') 
            
            printResults(final_results_dict)
            printValidationResults(nonexecuted_transactions)
        else:
              
            cerebro_list = []
            start = time.perf_counter()

            for stratKey in strategies_dict:
            
                cerebro = bt.Cerebro(optreturn=True, stdstats=False)
                cerebro_list.append(cerebro)
                stkwargs = strategies_dict[stratKey]['kwargs']

                addData(cerebro, args, symbolDataIndexes)
                cerebro.addstrategy(strategies_dict[stratKey]['strategy'], **stkwargs)
                setCerebroParameters(cerebro, args)
                addObservers(cerebro)
            
                stResults = cerebro.run()
            
                results_list = []    
                results_list.append(getAnalysisResults(stResults[0], args))
                final_results_dict[strategies_dict[stratKey]['strategy']] = results_list
                nonexecuted_transactions= validateResults(stResults[0])
        
            end = time.perf_counter()       
            print(f'Finished in {round(end-start, 2)} second(s)') 
        
            printResults(final_results_dict)
            printValidationResults(nonexecuted_transactions)
        
        
            if args.plot:
                for c in cerebro_list:
                    c.plot()

def parallel_strat(args, stratKey, strategies_dict, symbolDataIndexes):
    cerebro = bt.Cerebro(optreturn=True, stdstats=False)
    stkwargs = strategies_dict[stratKey]['kwargs']

    addData(cerebro, args, symbolDataIndexes)
    cerebro.addstrategy(strategies_dict[stratKey]['strategy'], **stkwargs)
    setCerebroParameters(cerebro, args)
    addObservers(cerebro)
            
    stResults = cerebro.run()
            
    results_list = []    
    results_list.append(getAnalysisResults(stResults[0], args))
    
    nonexecuted_transactions= validateResults(stResults[0])
    return [results_list, nonexecuted_transactions]
    

def getAnalysisResults(strategyResult, args):
    my_dict = strategyResult.analyzers.time_return.get_analysis()
    annual_returns = [v+1 for _, v in my_dict.items()]
    annualReturn = math.prod(annual_returns)
    
    try:
        cashWorth = strategyResult.cash_addition + args.cash
        endWorth = round(strategyResult.broker.get_value(), 2)
    except BaseException as err:
        cashWorth = endWorth = 0

    PnL = round(endWorth - cashWorth, 2)
    transactionsList = list(strategyResult.analyzers.transactions.get_analysis())
    years = (transactionsList[-1] - transactionsList[0]).days / 365.25

    compaund_annual_return = np.power(annualReturn, 1 / years)-1
    annualReturn = round(compaund_annual_return*100, 2)
    volatility = round(strategyResult.analyzers.volatility.get_analysis()['volatility']*100,2)
    sharpe = round(strategyResult.analyzers.sharperatio_a.get_analysis()['sharperatio'],2)
    drawDownPercentage = round(strategyResult.analyzers.drawdownperyear.get_analysis()['max']['drawdown'],2)
    drawDownPeriod = round(strategyResult.analyzers.drawdownperyear.get_analysis()['max']['len'] / 24,2)
    drawdownPerYear = strategyResult.analyzers.drawdownperyear.get_analysis()['drawDownsPerYear']
    
    return [    cashWorth,
                endWorth,
                PnL,
                annualReturn,
                volatility,
                sharpe,
                drawDownPercentage,
                drawDownPeriod,
                drawdownPerYear,
                annual_returns
            ]


def validateResults(strategyResult):
    # Validate the results
    trackedorders=[]
    nonexecuted_transactions = {}
    for tickerIndex in strategyResult.pastTransactions:
        transData = strategyResult.pastTransactions[tickerIndex]
        for transaction in transData['transactions'][0:-1]:
            res =  [order for order in strategyResult.broker.orders 
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

    return nonexecuted_transactions

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


    parser.add_argument('--fromdate', '-f', default='2017-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t', default='2021-12-31',
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


    parser.add_argument('--plot', '-p', action='store_false',
                        help='Plot the read data')

    parser.add_argument('--updatePrices', '-u', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='Plot using numfigs figures')

    parser.add_argument('--optimize', '-opt', default=1,
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()