# python internals
from __future__ import annotations
# internal packages
from .ntypes import *
from .cache import Cache
# external packages
import numpy as np
from scipy.special import genlaguerre as laguerre
from scipy.special import lpmv as legendre
from scipy.special import factorial as fact
from scipy.interpolate import griddata

class StateSpec:
    def __init__(self, n: int, l: int, m: int) -> None:
        if n < 1:
            raise ValueError("The value of the principal quantum number must be greater than 0.")
        if l >= n:
            raise ValueError(
                "The value of the secondary quantum number must be less than the value of the principal quantum number.")
        if m < -l or m > l:
            raise ValueError("The magnetic number modulus cannot be greater than the secondary quantum number modulus.")
        self.__n = n
        self.__l = l
        self.__m = m
    @property
    def n(self) -> int: return self.__n
    @property
    def l(self) -> int: return self.__l
    @property
    def m(self) -> int: return self.__m

class State:
    def __init__(self, spec: StateSpec) -> None:
        self.__specs = spec
        self.__cache = Cache()
    @property
    def specs(self) -> StateSpec:
        return self.__specs
    def wf_val(self, p: SphCoords, t: float = 0) -> carray_t:
        scale = 1.0
        px = np.asarray(legendre(abs(self.__specs.m), self.__specs.l, np.cos(p.theta)), dtype=complex)
        angle = (-1) ** abs(self.__specs.m) * np.sqrt(((2 * self.__specs.l + 1) * fact(self.__specs.l - abs(self.__specs.m))) / (4 * np.pi * fact(self.__specs.l + abs(self.__specs.m)))) * px * np.exp(1j * abs(self.__specs.m) * p.phi)
        la = np.asarray(laguerre(self.__specs.n - self.__specs.l - 1, 2 * self.__specs.l + 1)(2 * p.r / (self.__specs.n * scale)), dtype=npfloat_t)
        radius = p.r ** self.__specs.l * (2 / (self.__specs.n * scale)) ** (self.__specs.l + 1) * la * np.exp(-p.r / (self.__specs.n * scale))
        return np.asarray(radius * angle * np.exp(-1j*self.en_val()*t), dtype=npcomplex_t)
    def en_val(self) -> farray_t:
        mu = 1.0; alpha = 0.01; c = 300000.0
        return -mu * c ** 2 * (-1 + np.sqrt(1 + (2 * alpha ** 2) / (self.__specs.n - np.abs(self.__specs.l + 0.5) - 0.5 + np.sqrt((np.abs(self.__specs.l + 0.5) + 0.5) ** 2 - alpha ** 2))))

class Atom:
    def __init__(self, *args: State) -> None:
        self.__states = args
    def __points(self, dims: SphDims) -> SphCoords:
        rmax = 10 * max(state.specs.n for state in self.__states) ** 2
        r = np.linspace(0, rmax, dims.r_dim)
        theta = np.linspace(0, np.pi, dims.angle_dim)
        phi = np.linspace(0, 2 * np.pi, dims.angle_dim)
        return SphCoords(*(np.meshgrid(r, theta, phi, indexing='ij')),)
    def __mask(self, p: SphCoords, t: float = 0) -> farray_t:
        pr_sum = np.sum(np.array([np.abs(state.wf_val(p, t)) ** 2 for state in self.__states]), axis=0)
        cutoff = pr_sum.max() * 0.001
        return pr_sum > cutoff
    def pr_val(self, p: SphCoords, t: float = 0) ->  farray_t:
        psi = np.sum(np.array([state.wf_val(p, t) for state in self.__states], dtype=npcomplex_t), axis=0)
        return np.abs(psi) ** 2
    def sph_scatter(self, t: float = 0, dims: SphDims = SphDims(200, 160)) -> SphScatter:
        p = self.__points(dims)
        mask = self.__mask(p, t)
        masked_p = SphCoords(*(c[mask] for c in p))
        return SphScatter(*masked_p, self.pr_val(p, t)[mask])
    def cart_scatter(self, *args) -> CartScatter:
        el = self.sph_scatter(*args)
        return CartScatter(el.r * np.sin(el.theta) * np.cos(el.phi), el.r * np.sin(el.theta) * np.sin(el.phi), el.r * np.cos(el.theta), el.psi)
    def cart_grid(self, t: float = 0, method: interpolation_t = 'nearest', dims: CartDims = CartDims(150, 150, 150)) -> farray_t:
        sc = self.cart_scatter(t, dims.to_sph())
        xi = np.linspace(np.min(sc.x), np.max(sc.x), dims.x_dim)
        yi = np.linspace(np.min(sc.y), np.max(sc.y), dims.y_dim)
        zi = np.linspace(np.min(sc.z), np.max(sc.z), dims.z_dim)
        return griddata(
            np.column_stack((sc.x, sc.y, sc.z)),
            sc.psi,
            np.meshgrid(xi, yi, zi, indexing='ij'),
            method=method,
            fill_value=0.0
        )

__all__ = ['StateSpec', 'State', 'Atom']