# python internals
from __future__ import annotations
from typing import NamedTuple
# external packages
import numpy as np
import numpy.typing as npt

# type hints definitions
array_t = npt.NDArray[np.floating]
carray_t = npt.NDArray[np.complexfloating]

# type definitions
class SphPoints(NamedTuple): r: array_t; theta: array_t; phi: array_t
class CartPoints(NamedTuple): x: array_t; y: array_t; z: array_t
class SphGrid(NamedTuple): r: array_t; theta: array_t; phi: array_t; psi: array_t
class CartGrid(NamedTuple): x: array_t; y: array_t; z: array_t; psi: array_t
class GridDims(NamedTuple): r_dim: int; angle_dim: int;