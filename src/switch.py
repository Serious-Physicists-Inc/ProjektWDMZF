from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QCheckBox

class ToggleSwitch(QCheckBox):
    def __init__(self, parent: Optional[QCheckBox] = None, width: int = 50, height: int = 26, bg_color: str = "#4e5254", circle_color: str = "#ffffff", active_color: str = "#00BCff") -> None:
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._bg_color: str = bg_color
        self._circle_color: str = circle_color
        self._active_color: str = active_color

        self._circle_position: float = 3

        self.animation: QPropertyAnimation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(250)

        self.setText("")
        self.stateChanged.connect(self.start_transition)
    @pyqtProperty(float)
    def circle_position(self) -> float:
        return self._circle_position
    @circle_position.setter
    def circle_position(self, pos: float) -> None:
        self._circle_position = pos
        self.update()
    def start_transition(self, state: int) -> None:
        self.animation.stop()
        if state:
            self.animation.setEndValue(self.width() - self.height() + 3)
        else:
            self.animation.setEndValue(3)
        self.animation.start()
    def hitButton(self, pos) -> bool:
        return self.contentsRect().contains(pos)
    def paintEvent(self, e) -> None:
        p: QPainter = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color: QColor = QColor(self._active_color) if self.isChecked() else QColor(self._bg_color)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)

        radius: int = int(self.height() / 2)
        p.drawRoundedRect(0, 0, self.width(), self.height(), radius, radius)

        p.setBrush(QColor(self._circle_color))
        p.drawEllipse(QRectF(self._circle_position, 3, self.height() - 6, self.height() - 6))
        p.end()

__all__ = ['ToggleSwitch']
