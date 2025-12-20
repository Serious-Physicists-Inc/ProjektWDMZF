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
array_t = np.ndarray
farray_t = npt.NDArray[npfloat_t]
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
class SphCoords(NamedTuple): r: farray_t; theta: farray_t; phi: farray_t
class CartCoords(NamedTuple): x: farray_t; y: farray_t; z: farray_t
class SphScatter(NamedTuple):
    r: farray_t; theta: farray_t; phi: farray_t; psi: farray_t
    def coords(self) -> SphCoords: return SphCoords(self.r, self.theta, self.phi)
class CartScatter(NamedTuple):
    x: farray_t; y: farray_t; z: farray_t; psi: farray_t
    def coords(self) -> CartCoords: return CartCoords(self.x, self.y, self.z)

__all__ = ['npfloat_t', 'npuint_t', 'npcomplex_t', 'array_t', 'farray_t', 'uarray_t', 'carray_t', 'interpolation_t', 'colormap_t', 'SphCoords', 'CartDims', 'CartCoords', 'SphScatter', 'CartScatter', 'SphDims']