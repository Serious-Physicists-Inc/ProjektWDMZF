# python internals
from __future__ import annotations
from typing import Callable, Optional
import time
# external packages
from PyQt6.QtCore import QTimer, QObject

class Scheduler:
    def __init__(self, action: Callable[[], None], delay: float, parent: Optional[QObject] = None) -> None:
        if delay <= 0:
            raise ValueError("delay must be > 0")

        self.__action = action
        self.__delay = delay

        self.__busy = False
        self.__blocked_until: float = 0

        self.__last_tick: float = 0
        self.__frame_time: float = 0

        self.__timer = QTimer(parent)
        self.__timer.timeout.connect(self.__tick)
    def block(self, t: Optional[float] = None) -> None:
        self.__blocked_until = float('inf') if t is None else time.monotonic() + t
    def unblock(self) -> None:
        self.__blocked_until = 0
    def __tick(self) -> None:
        if self.__busy or time.monotonic() < self.__blocked_until: return

        curr_time = time.monotonic()
        self.__frame_time = curr_time - self.__last_tick if self.__last_tick > 0 else 0
        self.__last_tick = curr_time

        self.__busy = True
        try:
            self.__action()
        except Exception as e:
            print("Error during Scheduler tick:", e)
        finally:
            self.__busy = False
    def frame_time(self) -> float:
        return self.__frame_time
    def start(self) -> None:
        self.__timer.start(int(self.__delay * 1000))
    def stop(self) -> None:
        self.__timer.stop()

__all__ = ["Scheduler"]