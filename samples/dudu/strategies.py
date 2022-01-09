import math

import datetime #do not delete - for breakpoints
import backtrader as bt
from backtrader.order import Order
import numpy as np


class OldStrategy(bt.Strategy):
    '''
    Current transactions based on our history log
    '''
    params = dict(priceSize=1,
                  symbolsMapper=[],
                  detailedLog=False,
                  number_of_days=2,
                  keep_cash_percentage=0.2)
    
    def findTransactions(self, metaData, transactionDateRange):
        
        res = [trans for trans in metaData['transactions'][metaData['transactionIndex']:] if bt.date2num(trans.transactionDate) in transactionDateRange]
        return res
        

    def log(self, txt, force=False, dt=None):
        if self.p.detailedLog or force==True:
            ''' Logging function for this strategy'''
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))
            
    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datadate = self.datas[0].datetime 
        
        
        self.pastTransactions = {}
        i = 0
        for line in self.p.symbolsMapper:
            self.pastTransactions[i] = {'transactionIndex':0,
                                            'dataIndex':i, 
                                            'data':self.datas[i], 
                                            'transactions':line[1],
                                            'ticker':line[0]}
            i = i+1
        

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
   
    def notify_order(self, order):
        
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return



        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED,%.4f, Amount: %.4F, Cost: %.4f, Commission: %.4f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED,%.4f, Amount: %.2F, Cost: %.4f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.size,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected,order.Expired]:
            switcher = {order.Canceled:'Cancelled', 
                        order.Margin:'Margin',
                        order.Rejected:'Rejected',
                        order.Expired:'Expired'} 

            self.log('Order %s!!!,%.4f, Amount: %.4F, Cost: %.4f' %
                     (switcher[order.status],
                      order.created.price*self.p.priceSize,
                          order.created.size,
                          order.created.value*self.p.priceSize))
        

        self.order[order.p.data] = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl*self.p.priceSize, trade.pnlcomm))

    
    def next(self):

        if self.addCashForAllBuys():
            return

        if self.p.keep_cash_percentage > 0:
            self.removeCashOnNoTrades()

        for metaDataIndex in self.pastTransactions:
            metaData = self.pastTransactions[metaDataIndex]
            currentData = metaData['data']
            res = self.findTransactions(metaData, range(int(self.datadate[0]), int(self.datadate[0])+1))
            
            for trans in res:

                # Not yet in the market... we MIGHT BUY if...
                if trans:
                    validityDate = bt.num2date(self.datadate[0])+datetime.timedelta(days = 1)
                    if trans.transactionType == 'buy':
                        self.log('BUY CREATE %s, %.4f, Amount: %.4f, Cost: %.4f' % 
                                 (metaData['ticker'],
                                  trans.price * self.p.priceSize,
                                  trans.amount,
                                  trans.price * self.p.priceSize * trans.amount))
                        order = self.buy(exectype=Order.Limit,price=trans.price,size=trans.amount, data=currentData,valid=validityDate)
                        self.order[currentData] = order
                        self.signalBuy(trans.price * self.p.priceSize, trans.amount)
                        metaData['transactionIndex'] = metaData['transactionIndex'] + 1
                
                    elif self.getposition(data=currentData):
                        # Already in the market... we might sell
                        if trans.transactionType == 'sell':

                            self.log('SELL CREATE %s, %.4f, Amount: %.4f, Cost: %.4f' % 
                                        (metaData['ticker'],
                                        trans.price * self.p.priceSize,
                                        trans.amount, 
                                        trans.price * self.p.priceSize * trans.amount))

                            # Keep track of the created order to avoid a 2nd order
                            self.order[currentData] = self.sell(exectype=Order.Limit,price=trans.price,size=trans.amount, data=currentData,valid=validityDate)
                            self.signalSell(trans.price * self.p.priceSize, trans.amount)
                            metaData['transactionIndex'] = metaData['transactionIndex'] + 1

        if len(self.data) + 2 == self.data.buflen():
            for data in self.datas:
                self.log('CLOSE DATA %s'% (data._name))
                self.close(data=data)

    def addCashForAllBuys(self):
        additionalcash = 0
        
        additionalcash = self.getNeededCash(self.getPendingOrdersCash(range(int(self.datadate[0]), int(self.datadate[0])+1)))
        if  additionalcash > 0:
            self.addCash(additionalcash)
            return True
        return False

    def removeCashOnNoTrades(self):
        min_cash_to_remove = -100
        
        pendingOrders = self.getPendingOrdersCash(range(int(self.datadate[0]), int(self.datadate[0])+self.p.number_of_days+1))
        if  pendingOrders > 0:
            return False

        cash_percentage = self.broker.getcash() / self.broker.getvalue()
        if cash_percentage > self.p.keep_cash_percentage:
            cash_to_remove = self.p.keep_cash_percentage * self.broker.getvalue() - self.broker.getcash()
            if cash_to_remove < min_cash_to_remove: 
                self.addCash(cash_to_remove)
            return True

        return False

    def getPendingOrdersCash(self, date):
        pendingOrders = 0
        for metaDataIndex in self.pastTransactions:
            metaData = self.pastTransactions[metaDataIndex]
            pendingOrders = pendingOrders + sum([trans.price * trans.amount for trans in self.findTransactions(metaData, date) if not trans is None and trans.transactionType == 'buy'])
            
        return pendingOrders

    def addCash(self, cost): 
        self.broker.add_cash(cost)
        self.cash_addition = self.cash_addition + cost
        self.log('%.2f' % (cost), False)
            

    def getNeededCash(self, cost): 
        return max(0, math.ceil(cost - self.broker.get_cash()))

    def signalBuy(self, price, amount):
        pass

    def signalSell(self, price, amount):
        pass


class OldStrategyWithETFFencing(OldStrategy):
    '''
    Involve fencing with the trade
    '''
    params = (('symbol', ''), 
              ('priceSize', 1),
              ('symbolsMapper',{}))
    
    def __init__(self):
        super(OldStrategyWithETFFencing,self).__init__()
        self.fencingData = self.datas[len(self.datas)-1]
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
        
        fencingPercentage = 1
        minDaysFromLastFencingTransaction = 30
        minFencingCost = 5000

        invested = sum([order.p.data[0] * order.executed.size for order in self.broker.orders if order.status == order.Completed and order.p.data != self.fencingData])
        fencingCost = invested * fencingPercentage
        currentFencing = self.calculateCurrentFencing()
        
        if currentFencing['lastDate'] is None or self.datadate[0] - currentFencing['lastDate'] > minDaysFromLastFencingTransaction:
            fencingDelta = fencingCost - abs(currentFencing['sum'])

            if fencingDelta > minFencingCost:
                fencing_price = self.fencingData[0]
                fencing_amount = int(fencingDelta / fencing_price)

                if fencingDelta > 0:
                    self.log('SHORT SELL CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                                (fencing_price * self.p.priceSize,
                                fencing_amount,
                                fencing_price * fencing_amount))

                    self.order[self.fencingData] = self.sell(data=self.fencingData, exectype=Order.Limit, 
                                                        price=fencing_price, size = fencing_amount)
                elif fencingDelta < 0:
                    self.log('CLOSE SHORT CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                        (fencing_price * self.p.priceSize,
                        fencing_amount,
                        fencing_price * fencing_amount))

                    self.order[self.fencingData] = self.buy(data=self.fencingData, exectype=Order.Limit, 
                                                price=fencing_price, size = fencing_amount)
    
    def calculateCurrentFencing(self):
        ordersSum = 0
        lastOrderDate = None

        orders = [order for order in self.broker.orders 
                      if order.p.data is self.fencingData and 
                      order.issell() and
                      order.status in [order.Completed,order.Submitted, order.Accepted]] + \
                [order for order in self.broker.pending 
                                  if order.p.data is self.fencingData and 
                                  order.issell()]

        if len(orders) > 0:
            ordersSum = sum(order.executed.price * order.executed.size for order in orders)
            lastOrderDate = orders[len(orders)-1].created.dt
        
        return {'sum':ordersSum,
               'lastDate':lastOrderDate}

    def signalBuy(self, price, amount):
        i=0
    '''    
    def signalBuy(self, price, amount):
        orderValue = price * amount
        fencing_price = self.fencingData[0]
        fencing_amount = int(orderValue / fencing_price)

        self.log('SHORT SELL CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                    (fencing_price * self.p.priceSize,
                    fencing_amount,
                    orderValue))

            

        self.order[self.fencingData] = self.sell(data=self.fencingData, exectype=Order.Limit, 
                                            price=fencing_price, size = fencing_amount)

    def signalSell(self, price, amount):
        orderValue = price * amount
        fencing_price = self.fencingData[0]
        fencing_amount = int(orderValue / fencing_price)

        self.log('CLOSE SHORT CREATE, %.2f, Amount: %.2f, Cost: %.2f' % 
                (fencing_price * self.p.priceSize,
                fencing_amount,
                orderValue))

            

        self.order[self.fencingData] = self.buy(data=self.fencingData, exectype=Order.Limit, 
                                            price=fencing_price, size = fencing_amount)
      '''      
#SMAcrossover, EmaCrossLongShort
