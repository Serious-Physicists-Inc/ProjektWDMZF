# python internals
from __future__ import annotations
from typing import Tuple, Callable, Union, Optional
from dataclasses import dataclass
# internal packages
from .ntypes import *
from .scheduler import Scheduler
from .worker import Worker
from .view import WindowView, Hud, ColorBar
# external packages
from PyQt6.QtGui import QColor, QPalette
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

@dataclass
class WindowSpec:
    title: str = ""
    bg_color: Tuple[int, int, int] = (0, 0, 0)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    show_hud: bool = True
    show_colorbar: bool = True
    cmap_name: ColormapTypeT = 'plasma'

class Window:
    def __init__(self, spec: WindowSpec) -> None:
        self.__scheduler: Optional[Scheduler] = None
        self.__worker: Optional[Worker] = None
        self.__scale: float = 0

        self._view = WindowView()
        self._view.setWindowTitle(spec.title)
        self._view.mousePressOccurred.connect(self.__on_mouse_press)
        self._view.mouseReleaseOccurred.connect(self.__on_mouse_release)
        self._view.wheelScrollOccurred.connect(self.__on_wheel_scroll)
        self._view.resizeOccurred.connect(self.__on_resize)
        self._view.windowMinimizeOccurred.connect(self.__on_window_minimize)
        self._view.windowRestoreOccurred.connect(self.__on_window_restore)
        self._view.windowCloseOccurred.connect(self.__on_window_close)

        self._view.plot.setBackgroundColor(spec.bg_color)

        self._cmap = pg.colormap.get(spec.cmap_name)

        if spec.show_hud:
            self._view.hud = Hud(self._view)
            palette = self._view.hud.palette()
            palette.setColor(QPalette.ColorRole.WindowText, QColor(*spec.text_color))
            self._view.hud.setPalette(palette)

        if spec.show_colorbar:
            self._view.colorbar = ColorBar(self._view)
            self._view.colorbar.colormap = self._cmap
            self._view.colorbar.normalize_function = self._normalize
            palette = self._view.colorbar.palette()
            palette.setColor(QPalette.ColorRole.WindowText, QColor(*spec.text_color))
            self._view.colorbar.setPalette(palette)
            self._view.colorbar.show()

    def _normalize(self, val: NPFArrayT) -> NPFArrayT:
        v_log = np.log1p(np.maximum(val, 0.0))
        return v_log / np.log1p(self.__scale)
    def draw(self, val: Union[Scatter, Volume]) -> None:
        vmax = np.max(val.val)
        self.__scale = vmax
        if self._view.colorbar is not None:
            self._view.colorbar.set_scale(vmax)
            self._view.colorbar.set_val(val.val)
    def update(self, val: Union[Scatter, Volume]) -> None:
        if self._view.colorbar is not None:
            vmax = np.max(val.val)
            if self.__scale < vmax:
                self.__scale = vmax
                self._view.colorbar.set_scale(self.__scale)
                self._view.colorbar.set_val(val.val)
    def auto_update(self, function: Callable[[int], Union[Scatter, Volume]], fps: int) -> Scheduler:
        if self.__scheduler is not None:
            self.__scheduler.abort()
            self.__scheduler.deleteLater()
            self.__scheduler = None

        if self.__worker is not None:
            self.__worker.abort()
            self.__worker.deleteLater()
            self.__worker = None

        self.__scheduler = Scheduler(func=self.update, max_fps=fps, parent=self._view)
        self.__worker = Worker(func=function, buffer=self.__scheduler.buffer, parent=self._view)

        return self.__scheduler
    def show(self) -> None:
        self._view.showMaximized()
    def set_hud(self, text: str) -> None:
        if self._view.hud is None:
            raise RuntimeError("Hud nie został zainicjowany")
        self._view.hud.setText(text)
    def center(self) -> None: pass
    def snapshot(self) -> NPUArrayT:
        img = self._view.plot.grabFramebuffer()
        img = img.convertToFormat(img.Format.Format_RGBA8888)

        ptr = img.bits()
        ptr.setsize(img.sizeInBytes())

        arr = np.frombuffer(ptr, NPUintT).reshape((img.height(), img.width(), 4))
        return np.flipud(np.copy(arr))
    def abort(self) -> None:
        self._view.close()
    def __on_mouse_press(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block()
    def __on_mouse_release(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.unblock()
    def __on_wheel_scroll(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block(0.05)
    def __on_resize(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block(0.05)
    def __on_window_minimize(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block()
    def __on_window_restore(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.unblock()
            self.__scheduler.block(0.1)
    def __on_window_close(self) -> None:
        if self.__scheduler is not None:
            self.__scheduler.abort()
            self.__scheduler = None

        if self.__worker is not None:
            self.__worker.abort()
            self.__worker = None

class ScatterWindow(Window):
    def __init__(self, spec: WindowSpec = WindowSpec()) -> None:
        super().__init__(spec)
        self.__scatter: Optional[gl.GLScatterPlotItem] = None
    def __color(self, sc: Scatter) -> NPFArrayT:
        rgba = self._cmap.map(self._normalize(sc.val) ** 0.4, mode='float')
        rgba[:, 3] = 1.0
        return np.ascontiguousarray(rgba)
    @property
    def type(self): return "scatter"
    def draw(self, sc: Scatter) -> None:
        super().draw(sc)
        if self.__scatter is None:
            self.__scatter = gl.GLScatterPlotItem(pos=np.column_stack(sc.points), color=self.__color(sc), size=2)
            self.__scatter.setGLOptions('translucent')
            self._view.plot.addItem(self.__scatter)
        else:
            self.__scatter.setData(pos=np.column_stack(sc.points), color=self.__color(sc), size=2)
    def update(self, sc: Scatter) -> None:
        if self.__scatter is None:
            raise RuntimeError("Wykres punktowy nie został narysowany")

        super().update(sc)
        self.__scatter.setData(pos=np.column_stack(sc.points), color=self.__color(sc))
    def center(self) -> None:
        if self.__scatter is None: return

        center = self.__scatter.pos.mean(axis=0)
        self.__scatter.translate(-center[0], -center[1], -center[2])

class VolumeWindow(Window):
    def __init__(self, spec: WindowSpec = WindowSpec()) -> None:
        super().__init__(spec)
        self.__volume: Optional[gl.GLVolumeItem] = None
    def __color(self, vl: Volume) -> NPUArrayT:
        v_norm = self._normalize(vl.val)

        rgba = self._cmap.map(v_norm ** 0.4, mode='float').reshape((*v_norm.shape, 4))
        rgba[..., 3] = v_norm ** 0.5
        return np.ascontiguousarray((rgba * 255).astype(NPUintT))
    @property
    def type(self): return "volume"
    def draw(self, vl: Volume) -> None:
        super().draw(vl)
        if self.__volume is None:
            self.__volume = gl.GLVolumeItem(data=self.__color(vl), smooth=True, sliceDensity=1)
            self._view.plot.addItem(self.__volume)
        else:
            self.__volume.setData(data=self.__color(vl), smooth=True, sliceDensity=1)

        self.center()
    def update(self, vl: Volume) -> None:
        if self.__volume is None:
            raise RuntimeError("Wykres chmurowy nie został narysowany")

        super().update(vl)
        self.__volume.setData(self.__color(vl))
    def center(self) -> None:
        if self.__volume is None: return

        shape = np.array(self.__volume.data.shape, dtype=NPFloatT)
        center_offset = shape / 2
        self.__volume.translate(-center_offset[0], -center_offset[1], -center_offset[2])

__all__ = ['WindowSpec', 'ScatterWindow', 'VolumeWindow']