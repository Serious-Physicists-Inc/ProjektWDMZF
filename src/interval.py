# python internals
from __future__ import annotations
from typing import Callable, Optional
# external packages
from PyQt6.QtCore import QTimer, QObject

class Interval:
    def __init__(self, action: Callable[['Interval'], None], delay: float, parent: Optional[QObject]) -> None:
        if delay <= 0:
            raise ValueError("Delay must be greater than 0.")

        self.__delay = delay
        self.__action = action
        self.__parent = parent
        self.__timer: Optional[QTimer] = None
        self.__iter = 0
    def __del__(self):
        if self.__parent is None: self.stop()
    @property
    def iter(self) -> int:
        return self.__iter
    def __run(self) -> None:
        try:
            self.__action(self)
        except Exception as e:
            print("Error in Interval callback:", e)
        self.__iter += 1
    def start(self) -> None:
        if self.__timer is not None:
            raise RuntimeError("Interval has already been started.")
        self.__timer = QTimer(self.__parent)
        self.__timer.timeout.connect(self.__run)
        self.__timer.start(int(self.__delay*1000))
    def stop(self) -> None:
        if self.__timer is not None: self.__timer.stop()

__all__ = ['Interval']