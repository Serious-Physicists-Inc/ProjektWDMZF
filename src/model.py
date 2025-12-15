# internal packages
from ntypes import *
# external packages
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
    def wf_val(self, p: SphPoints, t: float = 0) -> carray_t:
        scale = 1.0
        px = np.asarray(legendre(abs(self.__specs['m']), self.__specs['l'], np.cos(p.theta)), dtype=complex)
        angle = (-1) ** abs(self.__specs['m']) * np.sqrt(((2 * self.__specs['l'] + 1)\
            * fact(self.__specs['l'] - abs(self.__specs['m']))) / (4 * np.pi * fact(self.__specs['l']\
            + abs(self.__specs['m'])))) * px * np.exp(1j * abs(self.__specs['m']) * p.phi)
        la = np.asarray(laguerre(self.__specs['n'] - self.__specs['l'] - 1, 2 * self.__specs['l'] + 1)(2 * p.r / (self.__specs['n'] * scale)), dtype=float)
        radius = p.r ** self.__specs['l'] * (2 / (self.__specs['n'] * scale)) ** (self.__specs['l'] + 1) * la * np.exp(-p.r / (self.__specs['n'] * scale))
        en = -0.5 / self.__specs['n'] ** 2
        return np.asarray(radius * angle * np.exp(-1j*en*t), dtype=complex)

class Atom:
    def __init__(self, *args: State) -> None:
        self.__states = args
    def __points(self, dims: GridDims) -> SphPoints:
        rmax = 10 * max(state.specs()['n'] for state in self.__states) ** 2
        r = np.linspace(0, rmax, dims.r_dim)
        theta = np.linspace(0, np.pi, dims.angle_dim)
        phi = np.linspace(0, 2 * np.pi, dims.angle_dim)
        return SphPoints(*(np.meshgrid(r, theta, phi, indexing='ij')),)
    def __mask(self, p: SphPoints, t: float = 0) -> array_t:
        pr_sum = np.sum((np.abs(state.wf_val(p, t)) ** 2 for state in self.__states), axis=0)
        cutoff = pr_sum.max() * 0.001
        return pr_sum > cutoff
    def pr_val(self, p: SphPoints, t: float = 0) ->  array_t:
        psi = np.sum(np.array([state.wf_val(p, t) for state in self.__states], dtype=complex), axis=0)
        return np.abs(psi) ** 2
    def sph_grid(self, t: float = 0, dims: GridDims = GridDims(180, 150)) -> SphGrid:
        p = self.__points(dims)
        mask = self.__mask(p, t)
        masked_p = SphPoints(*(c[mask] for c in p))
        return SphGrid(*masked_p, self.pr_val(p, t)[mask])
    def cart_grid(self, *args) -> CartGrid:
        el = self.sph_grid(*args)
        return CartGrid(el.r * np.sin(el.theta) * np.cos(el.phi), el.r * np.sin(el.theta) * np.sin(el.phi), el.r * np.cos(el.theta), el.psi)



