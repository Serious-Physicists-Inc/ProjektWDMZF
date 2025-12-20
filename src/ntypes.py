# python internals
from __future__ import annotations
from typing import NamedTuple, Literal
# external packages
import numpy as np
import numpy.typing as npt

# type hints definitions
npfloat_t = np.float64
npuint_t = np.uint8
npcomplex_t = np.complex64
array_t = npt.NDArray[npfloat_t]
uarray_t = npt.NDArray[npuint_t]
carray_t = npt.NDArray[npcomplex_t]
colormap_t = Literal['plasma', 'inferno', 'viridis', 'turbo', 'cividis']
interpolation_t = Literal['nearest', 'linear', 'cubic']

# type definitions
class SphDims(NamedTuple):
    r_dim: int; angle_dim: int
    def to_cart(self) -> CartDims:
        dim = self.r_dim + 2*self.angle_dim
        return CartDims(dim, dim, dim)
class CartDims(NamedTuple):
    x_dim: int; y_dim: int; z_dim: int
    def to_sph(self) -> SphDims:
        r_dim = max(self.x_dim, self.y_dim, self.z_dim)
        angle_dim = (self.x_dim + self.y_dim + self.z_dim - r_dim) // 2
        return SphDims(r_dim, angle_dim)
class SphCoords(NamedTuple): r: array_t; theta: array_t; phi: array_t
class CartCoords(NamedTuple): x: array_t; y: array_t; z: array_t
class SphScatter(NamedTuple):
    r: array_t; theta: array_t; phi: array_t; psi: array_t
    def coords(self) -> SphCoords: return SphCoords(self.r, self.theta, self.phi)
class CartScatter(NamedTuple):
    x: array_t; y: array_t; z: array_t; psi: array_t
    def coords(self) -> CartCoords: return CartCoords(self.x, self.y, self.z)

__all__ = ['array_t', 'uarray_t', 'carray_t', 'interpolation_t', 'colormap_t', 'SphCoords', 'CartDims', 'CartCoords', 'SphScatter', 'CartScatter', 'SphDims']