from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import sys
import argparse
import datetime

from os import listdir
from time import strftime
from backtrader.analyzers.transactions import Transactions

import numpy as np

import backtrader as bt
from backtrader.analyzers import (AnnualReturn, DrawDown, TimeDrawDown, SharpeRatio, Returns, SQN, TimeReturn,
                                  TradeAnalyzer, annualreturn)

from analyzers import *
from GetPrices import *
from backtrader.analyzers.sharpe import SharpeRatio_A
from strategies import *
from commissions import *
from strategies_plot import my_heatmap

def printResults(final_results_dict):

    headerKey                       = 'Parameter Name\t\t\t'
    underlineKey                    = '--------------\t\t\t'
    startWorthKey                   = 'Start Worth\t\t\t'
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
    '''
    yahooTickerStrings = ['DNA', 'ENTX', 'EDIT', 'CLGN', 'EYES', 'EXAS', 'MITC', 'MDWD', 'CHEK', 
				'AQB','RCEL', 'NNOX','ENLV','ASML', 'ALCRB.PA', 'NXFR.TA', 'MTLF.TA', 'BMLK.TA', 
				'NXGN.TA', 'PHGE.TA',  'ICCM.TA', 'CRTX', 'SPCE', 'SEDG', 'APLP.TA', 'AQUA.TA', 'PLX.TA', 'ENLT.TA', 'ECPA.TA', 'FVRR', 'SLGN.TA', 'UAL',  'PHGE', 'BVXV',
                'MMM','ATVI','GOOG','AMZN','AAPL','AVH.AX','BRK-B','BYND','CHKP','CTMX','EA','EQIX','FB','GE','GILD','GSK','INTC','LGND',
                'MU','NFLX','QCOM','RWLK','SGMO','TTWO','TSLA','TEVA','UPS','URGN','ENLV.TA','TEVA.TA','PSTI.TA']
    '''
    yahooTickerStrings = ['ICCM.TA']
    otherTickerStrings = []#['SRNG', 'MLNX', 'GHDX', 'JUNO', 'KITE', 'NTGN', 'ORBK']

    if updatePrices:
        for ticker in yahooTickerStrings:
            YahooFinancePricesBuilder().BuildFile(ticker, fromdate.strftime("%Y-%m-%d"))

    symbolDataIndexes = {}
    i=0
    for ticker in yahooTickerStrings:
        symbolDataIndexes[i] = ticker
        i = i+1

    for ticker in otherTickerStrings:
        symbolDataIndexes[i] = ticker
        i = i+1
    return symbolDataIndexes

def runstrategy():
    args = parse_args()

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    fencingpath = os.path.join(modpath, args.data + 'fencing_XBI' + '.csv')

    final_results_dict = {}
    strategies_list = [OldStrategy]
    #strategies_list = [OldStrategyWithETFFencing]

    symbolDataIndexes = loadSymbols(args.updatePrices, fromdate)

    for strat in strategies_list:
        
        cerebro = bt.Cerebro(optreturn=False)

        for index in symbolDataIndexes:
            datapath = os.path.join(modpath, args.data + symbolDataIndexes[index] + '.csv')
            data = bt.feeds.YahooFinanceCSVData(
                dataname=datapath,
                fromdate=fromdate,
                todate=todate,
                tframes=bt.TimeFrame.Minutes
            )
            cerebro.adddata(data, name=symbolDataIndexes[index])

        fencingData = bt.feeds.YahooFinanceCSVData(
            dataname=fencingpath,
            fromdate=fromdate,
            todate=todate,
            tframes=bt.TimeFrame.Minutes
        )

        

        cerebro.adddata(fencingData, name='Fencing')
        cerebro.addstrategy(strat, symbol=args.symbol, priceSize=1, symbolsMapper=symbolDataIndexes)

        results_list = []

        cerebro.broker.set_coc(True)
        # Need to set smarter the cash
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
        cerebro.addanalyzer(SQN)
        cerebro.addanalyzer(TimeReturn, _name='time_return', timeframe=tframes[args.tframe])
        cerebro.addanalyzer(SharpeRatio_A, timeframe=tframes[args.tframe], stddev_sample=True)
        cerebro.addanalyzer(Volatility)
        cerebro.addanalyzer(TradeAnalyzer)
        cerebro.addanalyzer(Transactions)
        cerebro.addanalyzer(DrawDownPerYear)
        
        st0 = cerebro.run()
        
        my_dict = st0[0].analyzers.time_return.get_analysis()
        annual_returns = [v for _, v in my_dict.items()]
        
        startWorth = args.cash
        endWorth = round(st0[0].broker.get_value(), 2)
        PnL = round(st0[0].broker.get_value() - args.cash, 2)
        transactionsList = list(st0[0].analyzers.transactions.get_analysis())
        years = (transactionsList[-1] - transactionsList[0]).days / 365.25

        compaund_annual_return = np.power(endWorth / startWorth, 1 / years)-1
        annualReturn = round(compaund_annual_return*100, 2)
        volatility = round(st0[0].analyzers.volatility.get_analysis()['volatility']*100,2)
        sharpe = round(st0[0].analyzers.sharperatio_a.get_analysis()['sharperatio'],2)
        drawDownPercentage = round(st0[0].analyzers.drawdownperyear.get_analysis()['max']['drawdown'],2)
        drawDownPeriod = round(st0[0].analyzers.drawdownperyear.get_analysis()['max']['len'] / 24,2)
        drawdownPerYear = st0[0].analyzers.drawdownperyear.get_analysis()['drawDownsPerYear']


        results_list.append([
            startWorth,
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

    # Average results for the different data feeds
    #arr = np.array(final_results_dict)
    #final_results_dict = [[int(val) if val.is_integer() else round(val, 2) for val in i] for i in arr.mean(0)]

    printResults(final_results_dict)

    if args.plot:
            cerebro.plot()
  

def parse_args():
    parser = argparse.ArgumentParser(description='TimeReturn')
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    parser.add_argument('--symbol', '-s',
                        default='ICCM.TA',
                        help='specific symbol to add to the system')

    parser.add_argument('--data', '-d',
                        default=os.path.join(modpath,'../../prices/'),
                        help='data to add to the system')


    parser.add_argument('--fromdate', '-f',
                        default='2018-05-06',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2021-12-19',
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

    parser.add_argument('--cash', default=100000 / 3.1, type=int,
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