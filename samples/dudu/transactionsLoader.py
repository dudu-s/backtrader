from datetime import date
import datetime
import csv
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
    startDate : date
    endDate : date

    
    def Load(self, symbol):
        transactions_ = []
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, '../../Transactions')

        header = True
        emptyDate = datetime.datetime.strptime('1/1/1900', '%m/%d/%Y')
        self.startDate = emptyDate
        self.endDate = emptyDate
        with open(os.path.join(datapath,symbol)  + '.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                if header == False:
                    if self.startDate == emptyDate:
                        self.startDate = datetime.datetime.strptime(row[1],'%m/%d/%Y')
                    self.endDate = datetime.datetime.strptime(row[1],'%m/%d/%Y')
                    transactions_.append(PastTransaction(row[0], datetime.datetime.strptime(row[1], '%m/%d/%Y'), row[3], row[2]))

                header = False
        
        return transactions_

    def Years(self):
        delta = self.endDate - self.startDate
        return delta.days / 365.25

if __name__ == '__main__':
    # For testing purposes only!
    TransactionsLoader().Load('ICCM.TA')