# python internals
from __future__ import annotations
from typing import Tuple, Union, Callable, Literal, Optional, Any
from dataclasses import dataclass
import sys
# internal packages
from .ntypes import interpolation_t, colormap_t, SphDims
from .model import StateSpec, State, Atom, AtomPlotter
from .plot import *
from .interval import *
# external packages
from PyQt6.QtWidgets import QApplication

@dataclass
class Settings:
    interactive: bool = True
    fps: int = 30
    speed: float = 1
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_colormap: colormap_t = 'plasma'
    plot_interpolation: interpolation_t = 'nearest'

app = QApplication(sys.argv)
settings: Settings = Settings()

def main() -> Tuple[Union[ScatterPlotWindow, VolumePlotWindow], Optional[Interval]]:
    states = (State(StateSpec(1, 0, 0)),State(StateSpec(2, 1, 0)))
    atom = Atom(*states)
    plotter = AtomPlotter(atom, SphDims(100, 100))

    plot_spec: PlotWindowSpec = PlotWindowSpec(
        title="Electron cloud of a hydrogen atom",
        cmap_name=settings.plot_colormap
    )
    if settings.plot_type == 'ScatterPlot':
        plot = ScatterPlotWindow(plot_spec)
        plot.draw(plotter.cart_scatter(0).masked())
    elif settings.plot_type == 'VolumePlot':
        plot = VolumePlotWindow(plot_spec)
        plot.draw(plotter.cart_grid(0, settings.plot_interpolation))
    else: raise ValueError(f"Unknown value of settings.plot_type: {settings.plot_type}")
    plot.show()

    interval: Optional[Interval] = None
    if settings.interactive:
        dt = 1.0 / settings.fps
        callback: Callable[[int], Any] = lambda i: plotter.cart_scatter(i*settings.speed*dt).masked() if settings.plot_type == 'ScatterPlot' else lambda j: plotter.cart_grid(j*settings.speed*dt, settings.plot_interpolation)
        interval = plot.auto_update(callback, dt)
        interval.start()

    return plot, interval

if __name__ == "__main__":
    res = main()

input("Naciśnij Enter, aby zakończyć...")