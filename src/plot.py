# python internals
from __future__ import annotations
from typing import Tuple, Callable, Union, Optional
from dataclasses import dataclass
# internal packages
from .ntypes import *
from .interval import *
# external packages
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

@dataclass
class PlotWindowSpec:
    title: str = ""
    bg_color: Tuple[int, int, int] = (0, 0, 0)
    show_grid: bool = False
    cmap_name: colormap_t = 'plasma'

class PlotWindow:
    def __init__(self, spec: PlotWindowSpec) -> None:
        self._view = gl.GLViewWidget()
        self._view.setWindowTitle(spec.title)
        self._view.setBackgroundColor(spec.bg_color)

        self._grid = None
        if spec.show_grid:
            self._grid = gl.GLGridItem()
            self._grid.scale(1, 1, 1)
            self._view.addItem(self._grid)

        self._cmap = pg.colormap.get(spec.cmap_name)

        self._view.setCameraPosition(distance = 10.0, elevation = 20.0, azimuth = 45.0)
    def draw(self, grid: Union[CartScatter, farray_t]) -> None:
        pass
    def update(self, grid: Union[CartScatter, farray_t]) -> None:
        pass
    def auto_update(self, function: Callable[[int], Union[CartScatter, farray_t]], dt: float) -> Interval:
        return Interval(lambda interval: self.update(function(interval.iter)), dt, self._view)
    def show(self) -> None:
        self._view.show()

class ScatterPlotWindow(PlotWindow):
    def __init__(self, spec: PlotWindowSpec = PlotWindowSpec()) -> None:
        super().__init__(spec)
        self.__scatter: Optional[gl.GLScatterPlotItem] = None
    def draw(self, sc: CartScatter) -> None:
        if self.__scatter is not None:
            self._view.removeItem(self.__scatter)
        self.__scatter = gl.GLScatterPlotItem(pos=np.column_stack(sc.coords()), color=self._cmap.map(sc.prob, mode='float'), size=1)
        self._view.addItem(self.__scatter)
    def update(self, sc: CartScatter) -> None:
        if self.__scatter is None:
            raise RuntimeError("Scatter plot has not been drawn yet.")
        self.__scatter.setData(color=self._cmap.map(sc.prob, mode='float'))

class VolumePlotWindow(PlotWindow):
    def __init__(self, spec: PlotWindowSpec = PlotWindowSpec()) -> None:
        super().__init__(spec)
        self.__volume: Optional[gl.GLVolumeItem] = None
    def draw(self, grid: CartGrid) -> None:
        if self.__volume is not None:
            self._view.removeItem(self.__volume)

        flatten = np.ravel(np.clip(grid.data, 0, None))
        rgba_flat = self._cmap.map(flatten, mode='float')
        rgba_flat[..., 3] = flatten / np.max(flatten)

        self.__volume = gl.GLVolumeItem(
            data=np.ascontiguousarray((rgba_flat.reshape((*np.shape(grid.data), 4)) * 255).astype(npuint_t)),
            smooth=True,
            sliceDensity=1
        )

        self._view.addItem(self.__volume)
    def update(self, grid: CartGrid) -> None:
        if self.__volume is None:
            raise RuntimeError("Volume plot has not been drawn yet")

        flatten = np.ravel(np.clip(grid.data, 0, None))

        rgba_flat = self._cmap.map(flatten, mode='float')
        rgba_flat[..., 3] = flatten / np.max(flatten)

        self.__volume.setData(np.ascontiguousarray((rgba_flat.reshape((*np.shape(grid.data), 4)) * 255).astype(npuint_t)))

__all__ = ['PlotWindowSpec', 'ScatterPlotWindow', 'VolumePlotWindow']