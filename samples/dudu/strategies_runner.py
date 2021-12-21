from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import sys
import argparse
import datetime

from os import listdir
from time import strftime

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

def printResults(final_results_list):
    print('Parameter Name\t\t\tOldStrategy\t\tNew Strategy')
    print('--------------\t\t\t-----------\t\t------------')
    print('Start Worth\t\t\t%.2F\t\t%.2F'% (final_results_list[0][0][0], final_results_list[1][0][0]) )
    print('End Worth\t\t\t%.2F\t\t%.2F'% (final_results_list[0][0][1], final_results_list[1][0][1]) )
    print('PNL\t\t\t\t%.2F\t\t%.2F'% (final_results_list[0][0][2], final_results_list[1][0][2]) )
    print('Annualised returns\t\t%.2F%%\t\t\t%.2F%%'% (final_results_list[0][0][3], final_results_list[1][0][3]) )
    print('Annualised volatility\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][4], final_results_list[1][0][4]) )
    print('Sharpe\t\t\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][5], final_results_list[1][0][5]) )
    print('Draw Down\t\t\t%.2F%%\t\t\t%.2F%%'% (final_results_list[0][0][6], final_results_list[1][0][6]) )
    print('Draw Down Period (Days)\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][7], final_results_list[1][0][7]) )
    
    drawdownsStrings = {}
    drawdownsPeriodStrings = {}
    for key in (final_results_list[0][0][8]):
        drawdownsStrings[key] = 'Draw Down %s\t\t\t%.2F%%'% (key,final_results_list[0][0][8][key].max.drawdown)
        drawdownsPeriodStrings[key] = 'Draw Down Period (Days) %s\t%.2F'% (key,final_results_list[0][0][8][key].max.len/24)
    
    for key in (final_results_list[1][0][8]):
        drawdownsStrings[key] = drawdownsStrings[key] + '\t\t\t%.2F%%'% (final_results_list[1][0][8][key].max.drawdown)
        drawdownsPeriodStrings[key] = drawdownsPeriodStrings[key] + '\t\t\t%.2F'% (final_results_list[1][0][8][key].max.len/24)

    for stringkey in drawdownsStrings:
        print(drawdownsStrings[stringkey])
        print(drawdownsPeriodStrings[stringkey])

def runstrategy():
    args = parse_args()

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, args.data + args.symbol + '.csv')

    final_results_list = []
    strategies_list = [OldStrategy, OldStrategy]

    if args.updatePrices:
        YahooFinancePricesBuilder().BuildFile(args.symbol, fromdate.strftime("%Y-%m-%d"))

    for strat in strategies_list:
        # Need to do something smarter that takes several files
        #path = os.path.join(datapath, f'{file}')
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=fromdate,
            todate=todate,
            tframes=bt.TimeFrame.Minutes
        )
        loader = TransactionsLoader()
        cerebro = bt.Cerebro(optreturn=False)

        # Need to handle several datas together
        cerebro.adddata(data, name='MyData0')
        cerebro.addstrategy(strat, symbol=args.symbol, priceSize=1, TransactionsLoader=loader)

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
        #cerebro.addanalyzer(TradeAnalyzer)
        cerebro.addanalyzer(DrawDownPerYear)
        
        st0 = cerebro.run()
        
        my_dict = st0[0].analyzers.time_return.get_analysis()
        annual_returns = [v for _, v in my_dict.items()]
        
        startWorth = args.cash
        endWorth = round(st0[0].broker.get_value(), 2)
        PnL = round(st0[0].broker.get_value() - args.cash, 2)
        compaund_annual_return = np.power(endWorth / startWorth, 1 / loader.Years())-1
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
        final_results_list.append(results_list)

    # Average results for the different data feeds
    arr = np.array(final_results_list)
    #final_results_list = [[int(val) if val.is_integer() else round(val, 2) for val in i] for i in arr.mean(0)]

    printResults(final_results_list)
    if args.plot:
        my_heatmap(final_results_list)


def parse_args():
    parser = argparse.ArgumentParser(description='TimeReturn')
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    parser.add_argument('--symbol', '-s',
                        default='ICCM.TA',
                        help='specific symbol to add to the system')

    parser.add_argument('--data', '-d',
                        default=os.path.join(modpath,'../../datas/'),
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

    parser.add_argument('--cash', default=100000, type=int,
                        help='Starting Cash')

    parser.add_argument('--plot', '-p', action='store_true',
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