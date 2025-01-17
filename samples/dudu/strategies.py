from datetime import date
import datetime

import backtrader as bt
import backtrader.indicators as btind
from backtrader.order import BuyOrder, Order, SellOrder
from transactionsLoader import *





class OldStrategy(bt.Strategy):
    '''
    Current transactions based on our history log
    '''
    params = (('symbol', ''), 
              ('priceSize', 1))
    

    def findTransaction(self, transactionDate, transactionIndex):
        
        #for trans in self.pastTransactions:
        trans = self.pastTransactions[transactionIndex]
        if int(transactionDate) == bt.date2num(trans.transactionDate):
            return trans
        return None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datadate = self.datas[0].datetime 
        self.transactionIndex=0
        
        self.pastTransactions = TransactionsLoader().Load(self.p.symbol)
        

        # Keep track of pending orders
        self.order = {}
        self.buyprice = None
        self.buycomm = None
   
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return


        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Amount: %.2F, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Amount: %.2F, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order[order.p.data] = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl*self.p.priceSize, trade.pnlcomm))

    def next(self):

        
        
        #if not self.position:
        trans = self.findTransaction(self.datadate[0], self.transactionIndex)

        # Not yet in the market... we MIGHT BUY if...
        if trans:
            if trans.transactionType == 'buy':
                if self.datas[0] in self.order and self.order[self.datas[0]]:
                    return

                self.log('BUY CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                         (trans.price * self.p.priceSize,
                          trans.amount,
                          trans.price * self.p.priceSize * trans.amount))
                order = self.buy(exectype=Order.Limit,price=trans.price,size=trans.amount, data=self.datas[0])
                self.order[self.datas[0]] = order
                self.transactionIndex = self.transactionIndex + 1

        if self.position:
            # Already in the market... we might sell
            if trans:
                if trans.transactionType == 'sell':

                    if self.order[self.datas[0]]:
                        return

                    self.log('SELL CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                             (trans.price * self.p.priceSize,
                              trans.amount, 
                              trans.price * self.p.priceSize * trans.amount))

                    # Keep track of the created order to avoid a 2nd order
                    self.order[self.datas[0]] = self.sell(exectype=Order.Limit,price=trans.price,size=trans.amount)
                    self.transactionIndex = self.transactionIndex + 1


class OldStrategyWithETFFencing(OldStrategy):
    '''
    Involve fencing with the trade
    '''
    params = (('symbol', ''), 
              ('priceSize', 1))
    
    def __init__(self):
        super(OldStrategyWithETFFencing,self).__init__()
        self.fencingData = self.datas[1]
        self.order[self.fencingData] = None

    def notify_order(self, order):
        
        if self.fencingData != order.p.data:
            super(OldStrategyWithETFFencing,self).notify_order(order)
            return

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Amount: %.2F, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SHORT SELL EXECUTED, Price: %.2f, Amount: %.2F, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))

            #self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order[order.p.data] = None
        

    def GetNextOrder(self):
        for data in self.order.keys():
            if not self.order[data] is None and data != self.fencingData:
                return self.order[data]
        return None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if trade.data == self.fencingData:
            self.log('SHORT OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl*self.p.priceSize, trade.pnlcomm))
        else:
            self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                     (trade.pnl*self.p.priceSize, trade.pnlcomm))

    def next(self):

        super(OldStrategyWithETFFencing,self).next()
        
        if all(value == None for value in self.order.values()):
            return
                
        order = self.GetNextOrder()
        if order is None or not self.order[self.fencingData] is None:
            return

        

        # Not yet in the market... we MIGHT BUY if...
        if order.isbuy():
            price = self.fencingData[0]
            orderValue = order.p.size * order.p.price
            amount = int(orderValue / price)

            self.log('SHORT SELL CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                        (price * self.p.priceSize,
                        amount,
                        orderValue))

            

            self.order[self.fencingData] = self.sell(data=self.fencingData, exectype=Order.Limit, 
                                                price=price, size = amount)

        if order.issell():
            # Already in the market... we might sell
            price = self.fencingData[0]
            orderValue = order.p.size * order.p.price
            amount = int(orderValue / price)

            self.log('CLOSE SHORT CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                        (price * self.p.priceSize,
                        amount,
                        orderValue))

            self.order[self.fencingData] = self.buy(data=self.fencingData, exectype=Order.Limit, 
                                                price=price, size = amount)
  
#SMAcrossover, EmaCrossLongShort
