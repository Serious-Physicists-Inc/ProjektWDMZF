import numpy as np
class State:
    @staticmethod
    def __val_specs(self, n:int, l:int, m:int):
        if n < 1:
            raise ValueError("Wartosc glownej liczby kwantowej musi byc wieksza od 0")
        elif l >= n:
            raise ValueError("Wartosc pobocznej liczby kwantowej musi byc mniejsza od wartosci glownej liczby głownej")
        elif m < -l or m > l:
            raise ValueError("Modul liczby magnetycznej nie moze byc wiekszy od modulu wartosci pobocznej liczby kwantowej")
    @overload
    def __init__(self, n:int, l:int, m:int):
        State.__val_specs(n, l, m)
        self.__specs = {'n': n, 'l': l, 'm': m}
    @overload
    def __init__(self, n1: int, l1: int, m1: int, n2: int, l2: int, m2: int):
        State.__val_specs(n1, l1, m1)
        self.__val_specs(n2, l2, m2)
        self.__specs = {'n': (n1, n2), 'l': (l1, l2), 'm': (m1, m2)}
    @overload
    def __init__(self, t_1:tuple[int, int, int], t_2:tuple[int, int, int]):
        State.__val_specs(t1[0], t1[1], t1[2])
        State.__val_specs(t2[0], t2[1], t2[2])
        self.__specs = {'n': (t1[0], t2[0]), 'l': (t1[1], t2[1]), 'm': (t1[2], t2[2])}
    def wfunc_val(self, R:float, Theta:float, Phi:float) -> np.ndarray:
        fLegendre = np.asarray(Legendre(abs(self.__specs['m']), l, np.cos(Theta)), dtype=complex)
        angle = (-1) ** abs(m) * np.sqrt(((2 * l + 1)\
            * fact(l - abs(self.__specs['m']))) / (4 * pi * fact(self.__specs['l']\
            + abs(self.__specs['m'])))) * P\
            * np.exp( 1j * abs(self.__specs['m']) * Phi)
        scale = 1.0
        fLaguerre = np.asarray(Laguerre(self.__specs['n'] - self.__specs['l'] - 1, 2 * self.__specs['l'] + 1)(2 * R / (self.__specs['n'] * scale)), dtype=float)
        radf = R ** l * (2 / (self.__specs['n'] * scale)) ** (self.__specs['l'] + 1) * L * np.exp(-R / (n * scale))

        Psi = radf * angle
        return np.asarray(Psi, dtype=complex)
