# python internals
from __future__ import annotations
from typing import Tuple, Union, Literal, Optional
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
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_colormap: ColormapT = 'plasma'

app = QApplication(sys.argv)
settings: Settings = Settings()

def main() -> Tuple[Union[ScatterPlotWindow, VolumePlotWindow], Optional[Scheduler]]:
    states = (State(StateSpec(2, 0, 0)),State(StateSpec(2, 1, 0)))
    atom = Atom(*states)

    plot_spec: PlotWindowSpec = PlotWindowSpec(
        title="Electron cloud of a hydrogen atom",
        cmap_name=settings.plot_colormap
    )

    plotter = Plotter(atom, SphDims(100, 100))
    if settings.plot_type == 'ScatterPlot':
        source = plotter.scatter()
        plot = ScatterPlotWindow(plot_spec)
    elif settings.plot_type == 'VolumePlot':
        source = plotter.volume()
        plot = VolumePlotWindow(plot_spec)
    else: raise ValueError(f"Unknown value of settings.plot_type: {settings.plot_type}")
    plot.draw(source.val().masked())
    plot.show()

    scheduler: Optional[Scheduler] = None
    if settings.interactive:
        dt = 1.0 / settings.fps
        fts = []
        def callback(i: int) -> Union[Scatter, Volume]:
            ft = scheduler.frame_time() if scheduler is not None else 0.0
            if ft > 0:
                fts.append(ft)
                if len(fts) > settings.fps: fts.pop(0)
            fps = 1.0 / (sum(fts) / len(fts)) if len(fts) > 0 else 0.0
            plot.set_hud(f"fps:      {fps:.3g}\nspec:\n"
                         + "\n".join(f"     ({s.n}, {s.l}, {s.m})" for s in atom.specs))

            return source.val(i * settings.speed * dt).masked()

        scheduler = plot.auto_update(callback, dt)
        scheduler.start()

    return plot, scheduler

if __name__ == "__main__":
    res = main()

input("Naciśnij Enter, aby zakończyć...")