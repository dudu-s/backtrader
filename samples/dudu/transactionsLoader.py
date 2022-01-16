from datetime import date
import datetime
import csv
import math
import os.path
import sys


from enum import Enum

class PastTransaction:
    transactionType: str
    transactionDate : date
    amount: int
    price: float

    def __init__(self, tt, td, am, pr):
        self.transactionType = tt
        self.transactionDate = td
        self.amount = int(float(am))
        self.price = float(pr)

class TransactionsLoader:

    def Load(self, symbol, option=False):
        transactions_ = []
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

        if option:
            datapath = os.path.join(modpath, '../../OptionsTransactions')
            filepath = os.path.join(datapath,symbol+"_OPTION")  + '.csv'
        else:
            datapath = os.path.join(modpath, '../../Transactions')
            filepath = os.path.join(datapath,symbol)  + '.csv'

        header = True
        with open(filepath, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                if header == False:
                    amount = math.floor(float(row[3]))
                    if (amount > 0):
                        transactions_.append(PastTransaction(row[0], datetime.datetime.strptime(row[1], '%m/%d/%Y'), amount, round(float(row[2]),4)))
                header = False
        
        return transactions_

if __name__ == '__main__':
    # For testing purposes only!
    TransactionsLoader().Load('ICCM.TA')