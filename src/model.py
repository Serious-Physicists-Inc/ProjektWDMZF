# python internal modules
from __future__ import annotations
from typing import Type
# python internal modules
import numpy as np
from scipy.special import genlaguerre as laguerre
from scipy.special import lpmv as legendre
from scipy.special import factorial as fact

class State:
    def __init__(self, n: int, l: int, m: int) -> None:
            if n < 1:
                raise ValueError("The value of the principal quantum number must be greater than 0.")
            if l >= n:
                raise ValueError("The value of the secondary quantum number must be less than the value of the principal quantum number.")
            if m < -l or m > l:
                raise ValueError("The magnetic number modulus cannot be greater than the secondary quantum number modulus.")
            self.__specs = {'n': n, 'l': l, 'm': m}
            return
    def specs(self) -> dict:
        return self.__specs.copy()
    def wf_val(self, r: float, theta: float, phi: float, t: float = 0) -> np.array:
        scale = 1.0
        p = np.asarray(legendre(abs(self.__specs['m']), self.__specs['l'], np.cos(theta)), dtype=complex)
        angle = (-1) ** abs(self.__specs['m']) * np.sqrt(((2 * self.__specs['l'] + 1)\
            * fact(self.__specs['l'] - abs(self.__specs['m']))) / (4 * np.pi * fact(self.__specs['l']\
            + abs(self.__specs['m'])))) * p * np.exp(1j * abs(self.__specs['m']) * phi)
        la = np.asarray(laguerre(self.__specs['n'] - self.__specs['l'] - 1, 2 * self.__specs['l'] + 1)(2 * r / (self.__specs['n'] * scale)), dtype=float)
        radius = r ** self.__specs['l'] * (2 / (self.__specs['n'] * scale)) ** (self.__specs['l'] + 1) * la * np.exp(-r / (self.__specs['n'] * scale))
        en = -0.5 / self.__specs['n'] ** 2
        return np.asarray(radius * angle * np.exp(-1j*en*t), dtype=complex)

class Atom:
    def __init__(self, *args:Type[State]) -> None:
        self.__states = args
    def __meshgrid(self, rdim: int, kdim: int) -> np.meshgrid:
        rmax = 10 * max(state.specs()['n'] for state in self.__states) ** 2
        r = np.linspace(0, rmax, rdim)
        theta = np.linspace(0, np.pi, kdim)
        phi = np.linspace(0, 2 * np.pi, kdim)
        return np.meshgrid(r, theta, phi, indexing='ij')
    def __mask(self, meshgrid: np.meshgrid, t: float = 0) -> np.array:
        pr_sum = sum(np.abs(state.wf_val(*meshgrid, t))**2 for state in self.__states)
        cutoff = pr_sum.max() * 0.001
        return pr_sum > cutoff
    @staticmethod
    def __to_cart_coords(self, r: float, theta: float, phi: float):
        return r * np.sin(theta) * np.cos(phi), r * np.sin(theta) * np.sin(phi), r * np.cos(theta)
    def pr_val(self, r: float, theta: float, phi: float, t: float = 0) ->  np.array:
        psi = np.sum(np.asarray((state.wf_val(r, theta, phi, t) for state in self.__states), dtype=float))
        return np.abs(psi) ** 2
    def polar_grid_raw(self, rdim: int = 180, kdim: int = 150, t: float = 0) -> np.array:
        return self.pr_val(*self.__meshgrid(rdim, kdim), t)
    def cart_grid_raw(self, *args) -> np.array:
        return Atom.__to_cart_coords(self.polar_grid_raw(*args))
    def polar_grid(self, rdim: int = 180, kdim: int = 150, t: float = 0) -> np.array:
        meshgrid = self.__meshgrid(rdim, kdim)
        mask = self.__mask(meshgrid, t)
        return self.pr_val(*meshgrid[mask], t)[mask]
    def cart_grid(self, *args) -> np.array:
        return Atom.__to_cart_coords() 



