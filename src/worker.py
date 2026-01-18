# python internals
from __future__ import annotations
from typing import Callable, Optional, Any
# internal packages
from .buffer import Buffer
from .ntypes import NPArrayT
# external packages
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
import numpy as np

class WorkerThread(QObject):
    resultReadyOccurred = pyqtSignal(object)
    errorOccurred = pyqtSignal(Exception)
    def __init__(self, func: Callable[[int], Any], parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.__func = func
    @pyqtSlot(int)
    def compute(self, iteration: int) -> None:
        try:
            result = self.__func(iteration).copy()
        except Exception as e:
            self.errorOccurred.emit(e)
            return

        self.resultReadyOccurred.emit(result)

class Worker(QObject):
    errorOccurred = pyqtSignal(Exception)
    __requestOccurred = pyqtSignal(int)
    def __init__(self, func: Callable[[int], Any], buffer: Buffer[Any], parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.__buffer = buffer
        self.__iter: int = 0
        self.__busy: bool = False

        self.__thread = QThread(self)
        self.__thread.setObjectName("WorkerThread")
        self.__worker = WorkerThread(func)
        self.__worker.moveToThread(self.__thread)

        self.__requestOccurred.connect(self.__worker.compute, Qt.ConnectionType.QueuedConnection)

        self.__worker.resultReadyOccurred.connect(self.__on_result)
        self.__worker.errorOccurred.connect(self.__on_error)

        self.__buffer.popOccurred.connect(self.__resume)
        self.__buffer.clearOccurred.connect(self.__resume)

        self.__thread.start()
        self.__step()
    def __resume(self) -> None:
        if not self.__busy: self.__step()
    def __step(self) -> None:
        if len(self.__buffer) >= self.__buffer.capacity:
            self.__busy = False
            return

        self.__busy = True
        self.__requestOccurred.emit(self.__iter)
        self.__iter += 1
    @pyqtSlot(object)
    def __on_result(self, value: NPArrayT) -> None:
        self.__buffer.push(value)
        self.__step()
    @pyqtSlot(Exception)
    def __on_error(self, error: Exception) -> None:
        self.errorOccurred.emit(error)
    def abort(self) -> None:
        self.__busy = True

        try:
            self.__buffer.popOccurred.disconnect(self.__resume)
            self.__buffer.clearOccurred.disconnect(self.__resume)
        except TypeError: pass

        try:
            self.__requestOccurred.disconnect()
        except TypeError: pass

        try:
            self.__worker.resultReadyOccurred.disconnect(self.__on_result)
            self.__worker.errorOccurred.disconnect(self.__on_error)
        except TypeError: pass

        if self.__thread.isRunning():
            self.__thread.quit()
            self.__thread.wait()

        self.__worker.deleteLater()
        self.__thread.deleteLater()

__all__ = ['Worker']
