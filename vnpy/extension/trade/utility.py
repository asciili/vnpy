from vnpy.trader.utility import ArrayManager

from typing import Callable, Dict, Tuple, Union, Optional

import numpy as np
import talib

class ExArrayManager(ArrayManager):
    def __init__(self, size: int = 100):
        """Constructor"""
        super().__init__(size)

    def sar(self, ix:int = 0, acceleration = 0.02, maximum = 0.2, array: bool = False) -> Union[float, np.ndarray]:
        """
        Stop and reverse.
        """
        result = talib.SAR(self.high, self.low, acceleration=acceleration, maximum=maximum)
        if array:
            return result
        return result[-1]

    def bbi(self, n1 = 3, n2 = 6, n3 = 12, n4 = 24) -> float:
        """
        bbi.
        """
        return (self.sma(n1) + self.sma(n2) + self.sma(n3) + self.sma(n4)) / 4

