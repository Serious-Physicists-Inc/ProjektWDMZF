# python internals
from __future__ import annotations
from typing import Optional
# internal packages
from .scheduler import Scheduler
# external packages
from PyQt6.QtCore import QEvent, Qt
import pyqtgraph.opengl as gl

class WindowView(gl.GLViewWidget):
    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self.__scheduler: Optional[Scheduler] = None
    @property
    def scheduler(self) -> Optional[Scheduler]:
        return self.__scheduler
    @scheduler.setter
    def scheduler(self, scheduler: Optional[Scheduler]) -> None:
        if self.__scheduler is not None:
            self.__scheduler.stop()
        self.__scheduler = scheduler
    def mouseMoveEvent(self, ev) -> None:
        if ev.buttons():
            if self.__scheduler is not None:
                self.__scheduler.block(0.05)
        super().mouseMoveEvent(ev)
    def wheelEvent(self, ev) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block(0.1)
        super().wheelEvent(ev)
    def changeEvent(self, ev) -> None:
        if ev.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                if self.__scheduler is not None:
                    self.__scheduler.block()
            else:
                if self.__scheduler is not None:
                    self.__scheduler.unblock()
        super().changeEvent(ev)
    def closeEvent(self, ev) -> None:
        if self.__scheduler is not None:
            self.__scheduler.stop()
            self.__scheduler = None
        super().closeEvent(ev)

__all__ = ['WindowView']