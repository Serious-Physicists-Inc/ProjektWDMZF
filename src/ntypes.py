# python internals
from __future__ import annotations
from typing import TypeAlias, Tuple, NamedTuple, Literal
from dataclasses import dataclass
import math
# external packages
from pyqtgraph import ColorMap
import numpy as np
import numpy.typing as npt

# type hints definitions
NPFloatT: TypeAlias = np.float32
NPIntT: TypeAlias = np.int32
NPUintT: TypeAlias = np.uint8
NPComplexT: TypeAlias = np.complex64
NPArrayT: TypeAlias = np.ndarray
NPFArrayT: TypeAlias = npt.NDArray[NPFloatT]
NPUArrayT: TypeAlias = npt.NDArray[NPUintT]
NPCArrayT: TypeAlias = npt.NDArray[NPComplexT]
NPBArrayT: TypeAlias = npt.NDArray[bool]
ColormapT: TypeAlias = ColorMap
ColormapTypeT: TypeAlias = Literal['plasma', 'inferno', 'viridis', 'turbo', 'cividis']

# type definitions
class SphDims(NamedTuple):
    r_dim: int; angle_dim: int
    def to_cart(self) -> CartDims:
        dim = math.ceil((self.r_dim + 2*self.angle_dim) / 3)
        dim = max(dim, self.r_dim, self.angle_dim)
        return CartDims(dim, dim, dim)

class CartDims(NamedTuple):
    x_dim: int; y_dim: int; z_dim: int
    def to_sph(self) -> SphDims:
        r_dim = max(self.x_dim, self.y_dim, self.z_dim)
        angle_dim = math.ceil((self.x_dim + self.y_dim + self.z_dim - r_dim) / 2)
        return SphDims(r_dim, angle_dim)

class SphPointsGrid(NamedTuple):
    r: NPFArrayT; theta: NPFArrayT; phi: NPFArrayT
    def ravel(self):
        return SphPoints(self.r.ravel(), self.theta.ravel(), self.phi.ravel())
class CartPointsGrid(NamedTuple):
    x: NPFArrayT; y: NPFArrayT; z: NPFArrayT
    def ravel(self):
        return CartPoints(self.x.ravel(), self.y.ravel(), self.z.ravel())

class SphPoints(NamedTuple): r: NPFArrayT; theta: NPFArrayT; phi: NPFArrayT
class CartPoints(NamedTuple): x: NPFArrayT; y: NPFArrayT; z: NPFArrayT

@dataclass(frozen=True, slots=True)
class Scatter:
    points: Tuple[np.ndarray, np.ndarray, np.ndarray]
    val: np.ndarray
    def __post_init__(self):
        for p in self.points:
            p.setflags(write=False)
        self.val.setflags(write=False)
    def copy(self) -> Scatter:
        return Scatter(points=tuple(np.copy(p) for p in self.points), val=np.copy(self.val))
    def masked(self, factor: float = 0.001) -> Scatter:
        cutoff = np.max(self.val) * factor
        mask = self.val > cutoff
        return Scatter(CartPoints(*(arr[mask] for arr in self.points)), self.val[mask])

@dataclass(frozen=True, slots=True)
class Volume:
    val: np.ndarray
    def __post_init__(self):
        self.val.setflags(write=False)
    def copy(self) -> Volume:
        return Volume(np.copy(self.val))
    def masked(self, factor: float = 0.001) -> Volume:
        cutoff = np.max(self.val) * factor
        return Volume(np.where(self.val > cutoff, self.val, 0.0))

__all__ = ['NPFloatT', 'NPIntT', 'NPUintT', 'NPComplexT', 'NPArrayT', 'NPFArrayT', 'NPUArrayT', 'NPCArrayT', 'NPBArrayT', 'ColormapT',
           'ColormapTypeT', 'SphDims', 'CartDims', 'SphPointsGrid', 'CartPointsGrid', 'SphPoints', 'CartPoints', 'Scatter', 'Volume']