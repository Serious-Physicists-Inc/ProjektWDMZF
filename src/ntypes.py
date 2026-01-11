# python internals
from __future__ import annotations
from typing import Tuple, NamedTuple, Literal
import math
# external packages
import numpy as np
import numpy.typing as npt

# type hints definitions
NPFloatT = np.float32
NPIntT = np.int32
NPUintT = np.uint8
NPComplexT = np.complex64
NPArrayT = np.ndarray
NPFArrayT = npt.NDArray[NPFloatT]
NPUArrayT = npt.NDArray[NPUintT]
NPCArrayT = npt.NDArray[NPComplexT]
NPBArrayT = npt.NDArray[bool]
ColormapT = Literal['plasma', 'inferno', 'viridis', 'turbo', 'cividis']

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

class Scatter(NamedTuple):
    points: CartPoints
    val: NPFArrayT
    def masked(self, factor: float = 0.001) -> Scatter:
        cutoff = np.max(self.val) * factor
        mask = self.val > cutoff
        return Scatter(CartPoints(*(arr[mask] for arr in self.points)), self.val[mask])

class Volume(NamedTuple):
    val: NPFArrayT
    def masked(self, factor: float = 0.001) -> Volume:
        cutoff = np.max(self.val) * factor
        return Volume(np.where(self.val > cutoff, self.val, 0.0))

__all__ = ['NPFloatT', 'NPIntT', 'NPUintT', 'NPComplexT', 'NPArrayT', 'NPFArrayT', 'NPUArrayT', 'NPCArrayT', 'NPBArrayT', 'ColormapT', 'SphDims', 'CartDims', 'SphPointsGrid', 'CartPointsGrid', 'SphPoints', 'CartPoints', 'Scatter', 'Volume']