# python internals
from __future__ import annotations
from typing import Optional
# internal packages
from .scheduler import Scheduler
# external packages
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout
import pyqtgraph.opengl as gl

class WindowView(gl.GLViewWidget):
    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self.__scheduler: Optional[Scheduler] = None

        self.setMinimumSize(400, 300)

        self.__hud = QLabel(self)
        font = QFont("Monospace", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.__hud.setFont(font)
        self.__hud.setAutoFillBackground(False)
        self.__hud.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.__hud.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 10)
        layout.addStretch()
        layout.addWidget(self.__hud, alignment=Qt.AlignmentFlag.AlignRight)
    @property
    def hud(self) -> QLabel:
        return self.__hud
    @property
    def scheduler(self) -> Optional[Scheduler]:
        return self.__scheduler
    @scheduler.setter
    def scheduler(self, scheduler: Optional[Scheduler]) -> None:
        if self.__scheduler is not None:
            self.__scheduler.stop()
        self.__scheduler = scheduler
    def mouseMoveEvent(self, ev) -> None:
        if ev.buttons() and self.__scheduler is not None:
            self.__scheduler.block(0.05)
        super().mouseMoveEvent(ev)
    def wheelEvent(self, ev) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block(0.1)
        super().wheelEvent(ev)
    def changeEvent(self, ev) -> None:
        if ev.type() == QEvent.Type.WindowStateChange:
            if self.__scheduler is not None:
                old = ev.oldState()
                new = self.windowState()

                if new & Qt.WindowState.WindowMinimized:
                    self.__scheduler.block()
                else:
                    changed = old ^ new
                    if ((old & Qt.WindowState.WindowMinimized) or
                            (changed & (Qt.WindowState.WindowMaximized | Qt.WindowState.WindowFullScreen))):
                        self.__scheduler.block(0.1)
        super().changeEvent(ev)
    def resizeEvent(self, ev) -> None:
        if self.__scheduler is not None:
            self.__scheduler.block(0.1)
        super().resizeEvent(ev)
    def closeEvent(self, ev) -> None:
        if self.__scheduler is not None:
            self.__scheduler.stop()
            self.__scheduler = None
        super().closeEvent(ev)

__all__ = ["WindowView"]