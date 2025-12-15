# python internals
from threading import Event, Thread
import time
from typing import Callable
# internal packages
from ntypes import *
# external packages
import numpy as np
import pyvista as pv

class Interval :
    def __init__(self, action, delay) -> None:
        self.i = 0
        self.delay = delay
        self.action = action
        self.stop_event = Event()
        self.thread = Thread(target = self.__set())
    def __del__(self):
        self.cancel()
    def __set(self) -> None:
        next_time = time.time() + self.delay
        while not self.stop_event.wait(next_time - time.time()):
            self.i += 1
            next_time += self.delay
            self.action(self.i)
    def start(self) -> None:
        self.thread.start()
    def cancel(self) :
        self.stop_event.set()

class Plot:
    def __init__(self) -> None:
        self.plotter = pv.Plotter()
        self.plotter.background_color = "black"
        self.plotter.window_size = (1920, 720)
        self.data = None
        return
    def draw(self, grid: CartGrid) -> None:
        points = np.column_stack((grid.x, grid.y, grid.z))
        self.data = pv.PolyData(points)
        self.data['prob'] = grid.psi

        self.plotter.add_mesh(self.data,
            scalars = 'prob',
            cmap = 'plasma',
            point_size=5.0,
            render_points_as_spheres = True,
            opacity = 'linear',
            show_scalar_bar = False)
    def update(self, grid: CartGrid) -> None:
        if self.data is None:
            raise RuntimeError("Cannot update plot that is not drawn.")
        self.data['prob'] = grid.psi
        self.plotter.update()
    def auto_update(self, function: Callable[[int], CartGrid], dt: float) -> Interval :
        interval = Interval(lambda i: self.update(function(i)), dt)
        return interval
    def show(self) -> None:
        self.plotter.show_axes()
        self.plotter.show()




