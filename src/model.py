# python internals
from __future__ import annotations
from typing import Tuple, Union
# internal packages
from .ntypes import *
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
        self.__spec = spec
    @property
    def spec(self) -> StateSpec:
        return self.__spec
    def wave_func(self, p: SphCoords) -> WaveFunction:
        return WaveFunction(self, p)
    def energy(self) -> farray_t:
        mu = 1.0; alpha = 0.01; c = 300000.0
        return -mu * c ** 2 * (-1 + np.sqrt(1 + (2 * alpha ** 2) / (self.spec.n - np.abs(self.spec.l + 0.5) - 0.5 + np.sqrt((np.abs(self.spec.l + 0.5) + 0.5) ** 2 - alpha ** 2))))

class WaveFunction:
    def __init__(self, state: State, p: SphCoords) -> None:
        scale = 1.0
        px = np.asarray(legendre(abs(state.spec.m), state.spec.l, np.cos(p.theta)), dtype=npcomplex_t)
        angle = (-1) ** abs(state.spec.m) * np.sqrt(((2*state.spec.l+1) * fact(state.spec.l - abs(state.spec.m))) / (4 * np.pi*fact(state.spec.l + abs(state.spec.m)))) * px * np.exp(1j*abs(state.spec.m)*p.phi)
        la = np.asarray(laguerre(state.spec.n-state.spec.l-1, 2*state.spec.l+1)(2*p.r/(state.spec.n * scale)),dtype=npfloat_t)
        radius = p.r ** state.spec.l * (2/(state.spec.n*scale)) ** (state.spec.l+1) * la * np.exp(-p.r / (state.spec.n*scale))
        self.__init_val: carray_t = radius * angle
        self.__state = state
    def val(self, t: float = 0.0) -> carray_t:
        return self.__init_val*np.exp(-1j*self.__state.energy()*t)

class Atom:
    def __init__(self, *args: State) -> None:
        self.__states = args
    @property
    def specs(self) -> Tuple[StateSpec, ...]:
        return tuple(state.spec for state in self.__states)
    def prob_func(self, p: SphCoords) ->  ProbFunction:
        return ProbFunction(self.__states, p)

class ProbFunction:
    def __init__(self, states: Tuple[State, ...], p: SphCoords) -> None:
        self.__wave_functions = tuple(state.wave_func(p) for state in states)
    def val(self, t: float = 0.0) -> farray_t:
        psi = np.sum(np.asarray(tuple(wave_fun.val(t) for wave_fun in self.__wave_functions), dtype=npcomplex_t), axis=0)
        return np.abs(psi) ** 2

class AtomPlotter:
    def __init__(self, atom: Atom, dims: Union[SphDims, CartDims]) -> None:
        self.__dims = dims

        rmax = 10 * max(spec.n for spec in atom.specs) ** 2
        r = np.linspace(0, rmax, self.__sph_dims.r_dim)
        theta = np.linspace(0, np.pi, self.__sph_dims.angle_dim)
        phi = np.linspace(0, 2 * np.pi, self.__sph_dims.angle_dim)
        self.__coords: SphCoords = SphCoords(*(np.meshgrid(r, theta, phi, indexing='ij')),)
        
        self.__prob_func: ProbFunction = atom.prob_func(self.__coords)
    @property
    def __sph_dims(self) -> SphDims:
        return self.__dims if type(self.__dims) is SphDims else self.__dims.to_sph()
    @property
    def __cart_dims(self) -> CartDims:
        return self.__dims if type(self.__dims) is CartDims else self.__dims.to_cart()
    def sph_scatter(self, t: float = 0) -> SphScatter:
        return SphScatter(*self.__coords, self.__prob_func.val(t))
    def cart_scatter(self, t: float = 0) -> CartScatter:
        sc = self.sph_scatter(t)
        return CartScatter(sc.r * np.sin(sc.theta) * np.cos(sc.phi), sc.r * np.sin(sc.theta) * np.sin(sc.phi), sc.r * np.cos(sc.theta), sc.prob)
    def cart_grid(self, t: float = 0, method: interpolation_t = 'nearest') -> CartGrid:
        sc = self.cart_scatter(t).masked()

        xi = np.linspace(np.min(sc.x), np.max(sc.x), self.__cart_dims.x_dim)
        yi = np.linspace(np.min(sc.y), np.max(sc.y), self.__cart_dims.y_dim)
        zi = np.linspace(np.min(sc.z), np.max(sc.z), self.__cart_dims.z_dim)

        grid_values = griddata(
            np.column_stack((sc.x, sc.y, sc.z)),
            sc.prob,
            np.meshgrid(xi, yi, zi, indexing='ij'),
            method=method,
            fill_value=0.0
        )

        return CartGrid(grid_values.reshape((len(xi), len(yi), len(zi))))

__all__ = ['StateSpec', 'State', 'WaveFunction', 'ProbFunction', 'Atom', 'AtomPlotter']