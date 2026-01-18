# python internals
from __future__ import annotations
from typing import Deque, Generic, TypeVar, Optional
from collections import deque
# external packages
from PyQt6.QtCore import QObject, QMutex, QMutexLocker, pyqtSignal

T = TypeVar("T")
class Buffer(QObject, Generic[T]):
    pushOccurred = pyqtSignal()
    popOccurred = pyqtSignal()
    clearOccurred = pyqtSignal()
    def __init__(self, capacity: int, parent: Optional[QObject] = None) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        super().__init__(parent)
        self.__mutex = QMutex()
        self.__buf: Deque[T] = deque(maxlen=capacity)
    def __len__(self) -> int:
        with QMutexLocker(self.__mutex):
            return len(self.__buf)
    @property
    def capacity(self) -> int:
        return self.__buf.maxlen
    def push(self, value: T) -> None:
        with QMutexLocker(self.__mutex):
            self.__buf.append(value)
        self.pushOccurred.emit()
    def pop(self) -> Optional[T]:
        with QMutexLocker(self.__mutex):
            if not self.__buf:
                return None
            value = self.__buf.popleft()

        self.popOccurred.emit()
        return value
    def clear(self) -> None:
        with QMutexLocker(self.__mutex):
            self.__buf.clear()
        self.clearOccurred.emit()

__all__ = ['Buffer']