# python internal modules
from __future__ import annotations
from typing import overload
# python internal modules
import numpy as np
from scipy.special import genlaguerre as Laguerre
from scipy.special import lpmv as Legendre
from scipy.special import factorial as fact

class State:
    @staticmethod
    def __val_sp(n:int, l:int, m:int) -> None:
        if n < 1:
            raise ValueError("The value of the principal quantum number must be greater than 0.")
        if l >= n:
            raise ValueError("The value of the secondary quantum number must be less than the value of the principal quantum number.")
        if m < -l or m > l:
            raise ValueError("The magnetic number modulus cannot be greater than the secondary quantum number modulus.")
    @overload
    def __init__(self, n: int, l: int, m: int) -> None: ...
    @overload
    def __init__(self, t1: tuple[int, int, int], t2: tuple[int, int, int]) -> None: ...
    def __init__(self, *args):
        # __init__(self, n: int, l: int, m: int) -> None: ...
        if len(args) == 3 and all(type(a) is int for a in args):
            n, l, m = args
            State.__val_sp(n, l, m)
            self.__sp = {'n': n, 'l': l, 'm': m}
            return
        # __init__(self, t1: tuple[int, int, int], t2: tuple[int, int, int]) -> None: ...
        if len(args) == 2 and all(isinstance(a, tuple) and len(a) == 3 for a in args):
            t1, t2 = args
            State.__val_sp(*t1[0])
            State.__val_sp(*t2[1])
            self.__sp = {
                'n': (t1[0], t2[0]),
                'l': (t1[1], t2[1]),
                'm': (t1[2], t2[2])
            }
            return
        raise TypeError("Invalid initializer signature for State")
    def wf_val(self, r:float, theta:float, phi:float, t:float = 0) -> np.array: return
    def pr_val(self, r:float, theta:float, phi:float, t:float = 0) ->  np.array:
        psi = self.wf_val(r, theta, phi, t)
        pr = np.abs(psi) ** 2
        return np.asarray(pr, dtype=float)

