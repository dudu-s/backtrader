from datetime import date
import math

import backtrader as bt
from backtrader.order import Order
from transactionsLoader import *


class OldStrategy(bt.Strategy):
    '''
    Current transactions based on our history log
    '''
    params = (('symbol', ''), 
              ('priceSize', 1),
              ('symbolsMapper',{}))
    
    def findTransactions(self, metaData, transactionDate):
        
        res = [trans for trans in metaData['transactions'][metaData['transactionIndex']:] if int(transactionDate) == bt.date2num(trans.transactionDate)]
        return res
        

    def log(self, txt, force=False, dt=None):
        #if force==True:
            ''' Logging function for this strategy'''
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datadate = self.datas[0].datetime 
        
        self.pastTransactions = {}
        for index in self.p.symbolsMapper:
            self.pastTransactions[index] = {'transactionIndex':0,
                                            'dataIndex':index, 
                                            'data':self.datas[index], 
                                            'transactions':TransactionsLoader().Load(self.p.symbolsMapper[index])}
        

        # Keep track of pending orders
        self.order = {}
        self.buyprice = None
        self.buycomm = None
        self.cash_addition = 0


        # Indicators for the plotting show
        #bt.indicators.PercentChange(self.datas[0], period = 3)
        #bt.indicators.StochasticSlow(self.datas[0])
        #bt.indicators.MACDHisto(self.datas[0])
        #rsi = bt.indicators.RSI(self.datas[0], period=3)
        #bt.indicators.SmoothedMovingAverage(rsi, period=3)
        #bt.indicators.ATR(self.datas[0], plot=False,period=3)
    
    '''
    def notify_fund(self, cash, value, fundvalue, shares):
        self.log('%.4f,%.4F,%.4f,%.4f' %
                    (cash, value, fundvalue, shares), True)
    '''

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

        if self.addCashForAllBuys():
            return

        for metaDataIndex in self.pastTransactions:
            metaData = self.pastTransactions[metaDataIndex]
            currentData = metaData['data']
            res = self.findTransactions(metaData, self.datadate[0])
            
            for trans in res:

                # Not yet in the market... we MIGHT BUY if...
                if trans:
                    if trans.transactionType == 'buy':
                        self.log('BUY CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                                 (trans.price * self.p.priceSize,
                                  trans.amount,
                                  trans.price * self.p.priceSize * trans.amount))
                        order = self.buy(exectype=Order.Limit,price=trans.price,size=trans.amount, data=currentData)
                        self.order[currentData] = order
                        metaData['transactionIndex'] = metaData['transactionIndex'] + 1
                
                if self.position:
                    # Already in the market... we might sell
                    if trans:
                        if trans.transactionType == 'sell':

                            self.log('SELL CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                                     (trans.price * self.p.priceSize,
                                      trans.amount, 
                                      trans.price * self.p.priceSize * trans.amount))

                            # Keep track of the created order to avoid a 2nd order
                            self.order[currentData] = self.sell(exectype=Order.Limit,price=trans.price,size=trans.amount)
                            metaData['transactionIndex'] = metaData['transactionIndex'] + 1
        

        if len(self.data) == self.data.buflen():
            self.close(data=self.datas[0])
        
    def addCashForAllBuys(self):
        additionalcash = 0
        pendingOrders = 0
        for metaDataIndex in self.pastTransactions:
            metaData = self.pastTransactions[metaDataIndex]
            res = self.findTransactions(metaData, self.datadate[0])
            
            for trans in res:

                # Not yet in the market... we MIGHT BUY if...
                if trans:
                    if trans.transactionType == 'buy':
                        pendingOrders = pendingOrders + (trans.price * trans.amount)
                        
        
        additionalcash = self.getNeededCash(pendingOrders)
        if  additionalcash > 0:
            self.addCash(additionalcash)
            return True
        return False
        
    def addCash(self, cost): 
        self.broker.add_cash(cost)
        self.cash_addition = self.cash_addition + cost
        self.log('%.2f' % (cost), False)
            

    def getNeededCash(self, cost): 
        return max(0, math.ceil(cost - self.broker.get_cash()))


class OldStrategyWithETFFencing(OldStrategy):
    '''
    Involve fencing with the trade
    '''
    params = (('symbol', ''), 
              ('priceSize', 1),
              ('symbolsMapper',{}))
    
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
