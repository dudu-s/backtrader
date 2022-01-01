import backtrader as bt


class CashObserver(bt.observer.Observer):
    alias = ('CashValue',)
    lines = ('cash', 'value')

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        
        self.lines.cash[0] = self._owner.broker.getcash()
        self.lines.value[0] = value = self._owner.broker.getvalue()

class FundObserver(bt.observer.Observer):
    alias = ('FundValue',)
    lines = ('shares', 'fundvalue')

    plotinfo = dict(plot=True, subplot=True)

    def next(self):
        self.lines.shares[0] = self._owner.broker.get_fundshares()
        self.lines.fundvalue[0] = value = self._owner.broker.get_fundvalue()