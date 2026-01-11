# python internals
from __future__ import annotations
from typing import Tuple, Callable, Union, Optional
from dataclasses import dataclass
# internal packages
from .debug import debug_time
from .ntypes import *
from .scheduler import Scheduler
from .worker import Worker
from .view import WindowView
# external packages
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

@dataclass
class PlotWindowSpec:
    title: str = ""
    bg_color: Tuple[int, int, int] = (0, 0, 0)
    cmap_name: ColormapT = 'plasma'

class PlotWindow:
    def __init__(self, spec: PlotWindowSpec) -> None:
        self._view = WindowView()
        self._view.setWindowTitle(spec.title)
        self._view.setBackgroundColor(spec.bg_color)
        self._view.setCameraPosition(distance=10.0, elevation=20.0, azimuth=45.0)

        self._cmap = pg.colormap.get(spec.cmap_name)
    def draw(self, val: Union[Scatter, Volume]) -> None: pass
    def update(self, val: Union[Scatter, Volume]) -> None: pass
    def auto_update(self, function: Callable[[int], Union[Scatter, Volume]], dt: float) -> Scheduler:
        worker = Worker(function, parent=self._view)
        worker.resultReady.connect(self.update)

        self._view.scheduler = Scheduler(action=worker.step, delay=dt, parent=self._view)
        self._view.scheduler.start()
        return self._view.scheduler
    def show(self) -> None:
        self._view.show()
    def center(self) -> None: pass
    def snapshot(self) -> NPUArrayT:
        img = self._view.grabFramebuffer()
        img = img.convertToFormat(img.Format.Format_RGBA8888)

        ptr = img.bits()
        ptr.setsize(img.sizeInBytes())

        arr = np.frombuffer(ptr, NPUintT).reshape((img.height(), img.width(), 4))
        return np.flipud(np.copy(arr))

class ScatterPlotWindow(PlotWindow):
    def __init__(self, spec: PlotWindowSpec = PlotWindowSpec()) -> None:
        super().__init__(spec)
        self.__scatter: Optional[gl.GLScatterPlotItem] = None

    def __color(self, sc: Scatter) -> NPFArrayT:
        v = np.maximum(sc.val, 0.0)
        v_log = np.log1p(v)
        vmax = np.max(v_log)
        v_norm = v_log / vmax if vmax > 0 else v_log

        gamma = 0.4
        rgba = self._cmap.map(v_norm ** gamma, mode='float')
        rgba[:, 3] = 1.0
        return np.ascontiguousarray(rgba)
    @debug_time
    def draw(self, sc: Scatter) -> None:
        if self.__scatter is not None:
            self._view.removeItem(self.__scatter)

        self.__scatter = gl.GLScatterPlotItem(pos=np.column_stack(sc.points), color=self.__color(sc), size=2)
        self.__scatter.setGLOptions('translucent')
        self._view.addItem(self.__scatter)
    @debug_time
    def update(self, sc: Scatter) -> None:
        if self.__scatter is None:
            raise RuntimeError("Scatter plot has not been drawn yet.")

        self.__scatter.setData(pos=np.column_stack(sc.points), color=self.__color(sc))
    def center(self) -> None:
        if self.__scatter is None: return

        center = self.__scatter.pos.mean(axis=0)
        self.__scatter.translate(-center[0], -center[1], -center[2])

class VolumePlotWindow(PlotWindow):
    def __init__(self, spec: PlotWindowSpec = PlotWindowSpec()) -> None:
        super().__init__(spec)
        self.__volume: Optional[gl.GLVolumeItem] = None
    def __color(self, vl: Volume) -> NPUArrayT:
        v_log = np.log1p(np.maximum(vl.val, 0.0))
        v_norm = v_log / np.max(v_log)
        rgba = self._cmap.map(v_norm, mode='float').reshape((*v_norm.shape, 4))
        rgba[..., 3] = v_norm
        return np.ascontiguousarray((rgba * 255).astype(NPUintT))
    @debug_time
    def draw(self, vl: Volume) -> None:
        if self.__volume is not None:
            self._view.removeItem(self.__volume)
        self.__volume = gl.GLVolumeItem(data=self.__color(vl), smooth=True, sliceDensity=1)

        self.center()
        self._view.addItem(self.__volume)
    @debug_time
    def update(self, vl: Volume) -> None:
        if self.__volume is None:
            raise RuntimeError("Volume plot has not been drawn yet")

        self.__volume.setData(self.__color(vl))
    def center(self) -> None:
        if self.__volume is None: return

        shape = np.array(self.__volume.data.shape, dtype=NPFloatT)
        center_offset = shape / 2
        self.__volume.translate(-center_offset[0], -center_offset[1], -center_offset[2])

__all__ = ['PlotWindowSpec', 'ScatterPlotWindow', 'VolumePlotWindow']