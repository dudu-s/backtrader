from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


class St(bt.SignalStrategy):
    params = dict(
        cash2add=None,
        cashonday=15,
        pfast=10,
        pslow=30,
        trade=False,
    )

    def __init__(self):
        self.add_timer(when=bt.Timer.SESSION_END, monthdays=[self.p.cashonday])

        sma1 = bt.ind.SMA(period=self.p.pfast)
        sma2 = bt.ind.SMA(period=self.p.pslow)
        signal = bt.ind.CrossOver(sma1, sma2)
        if self.p.trade:
            self.signal_add(bt.SIGNAL_LONGSHORT, signal)

    def notify_timer(self, timer, when, *args, **kwargs):
        # no need to check the timer, there is only one
        if self.p.cash2add is not None:
            self.broker.add_cash(self.p.cash2add)

    def next(self):
        pass


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))
    #cerebro.broker.set_fundmode(True)

    # Sizer
    cerebro.addsizer(bt.sizers.PercentSizer,
                     **eval('dict(' + args.sizer + ')'))

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))

    cerebro.addobserver(bt.observers.FundValue)
    cerebro.addobserver(bt.observers.FundShares)

    ankwargs = dict(timeframe=bt.TimeFrame.Years)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, **ankwargs)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, fund=True, **ankwargs)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, fund=False, **ankwargs)

    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Fund Tracking Sample'
        )
    )

    parser.add_argument('--data0', default='C:/PythonScripts/Projects/BackTrader/datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
