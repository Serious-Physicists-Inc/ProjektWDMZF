# python internals
from __future__ import annotations
from typing import Tuple, Union, Callable, Literal, Optional
from dataclasses import dataclass
import sys
# internal packages
from .ntypes import ColormapT, SphDims, Scatter, Volume
from .model import StateSpec, State, Atom, Plotter
from .scheduler import Scheduler
from .plot import *
# external packages
from PyQt6.QtWidgets import QApplication

@dataclass
class Settings:
    interactive: bool = True
    fps: int = 20
    speed: float = 1
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'VolumePlot'
    plot_colormap: ColormapT = 'plasma'

app = QApplication(sys.argv)
settings: Settings = Settings()

def main() -> Tuple[Union[ScatterPlotWindow, VolumePlotWindow], Optional[Scheduler]]:
    states = (State(StateSpec(1, 0, 0)),State(StateSpec(2, 1, 0)))
    atom = Atom(*states)

    plot_spec: PlotWindowSpec = PlotWindowSpec(
        title="Electron cloud of a hydrogen atom",
        cmap_name=settings.plot_colormap
    )

    if settings.plot_type == 'ScatterPlot':
        plotter = Plotter(atom, SphDims(100, 100))
        source = plotter.scatter()

        plot = ScatterPlotWindow(plot_spec)
        plot.draw(source.val().masked())
    elif settings.plot_type == 'VolumePlot':
        plotter = Plotter(atom, SphDims(100, 100))
        source = plotter.volume()

        plot = VolumePlotWindow(plot_spec)
        plot.draw(source.val().masked())
    else: raise ValueError(f"Unknown value of settings.plot_type: {settings.plot_type}")
    plot.show()

    scheduler: Optional[Scheduler] = None
    if settings.interactive:
        dt = 1.0 / settings.fps
        callback: Callable[[int], Union[Scatter, Volume]] = (lambda i: source.val(i * settings.speed * dt).masked()) if settings.plot_type == 'ScatterPlot' else (lambda j: source.val(j * settings.speed * dt).masked())
        scheduler = plot.auto_update(callback, dt)
        scheduler.start()

    return plot, scheduler

if __name__ == "__main__":
    res = main()

input("Naciśnij Enter, aby zakończyć...")