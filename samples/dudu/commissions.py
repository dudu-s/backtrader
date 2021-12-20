import backtrader as bt


class DegiroCommission(bt.CommInfoBase):
    params = (('per_share', 0.004), ('flat', 0.5),)

    def _getcommission(self, size, price, pseudoexec):
        return self.p.flat + abs(size) * self.p.per_share

class PoalimCommission(bt.CommInfoBase):
    params = (('per_share', 0.001), ('min', 10),)

    def _getcommission(self, size, price, pseudoexec):
        return max(self.p.min, abs(size) * abs(price) * self.p.per_share)