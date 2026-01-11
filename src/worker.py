# python internals
from __future__ import annotations
from typing import Callable, Optional, Any
# external packages
from PyQt6.QtCore import QObject, pyqtSignal

class Worker(QObject):
    resultReady = pyqtSignal(object)
    def __init__(self, func: Callable[[int], Any], parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._func: Callable[[int], Any] = func
        self.__iter: int = 0
    @property
    def iter(self) -> int:
        return self.__iter
    def step(self) -> None:
        try:
            result = self._func(self.__iter)
        except Exception as e:
            print("Error during Worker step:", e)
            return
        self.__iter += 1
        self.resultReady.emit(result)

__all__ = ["Worker"]
