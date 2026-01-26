# python internals
from __future__ import annotations
from typing import Tuple, Union, Literal, Optional
from dataclasses import dataclass
import sys
# internal packages
from src.ntypes import ColormapTypeT, SphDims, Scatter, Volume
from src.model import StateSpec, State, Atom, Plotter
from src.scheduler import Scheduler
from src.plot import *
# external packages
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QApplication

QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

@dataclass
class Settings:
    fps: int = 25
    speed: float = 0.25
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_dims: SphDims = SphDims(100, 100)
    plot_colormap: ColormapTypeT = 'plasma'
    show_hud: bool = True
    show_colorbar: bool = True

settings: Settings = Settings()

def main() -> Tuple[Union[ScatterWindow, VolumeWindow], Optional[Scheduler]]:
    states = (State(StateSpec(2, 0, 0)), State(StateSpec(2, 1, 0)))
    atom = Atom(*states)

    plot_spec: WindowSpec = WindowSpec(
        title="Chmura elektronowa atomu wodoru",
        cmap_name=settings.plot_colormap,
        show_hud=settings.show_hud,
        show_colorbar=settings.show_colorbar
    )

    plotter = Plotter(atom, settings.plot_dims)
    if settings.plot_type == 'ScatterPlot':
        source = plotter.scatter()
        plot = ScatterWindow(plot_spec)
    elif settings.plot_type == 'VolumePlot':
        source = plotter.volume()
        plot = VolumeWindow(plot_spec)
    else: raise ValueError("Ustawiono nieprawidłowy typ wykresu")
    plot.draw(source.val().masked())
    plot.show()

    scheduler: Optional[Scheduler] = None
    def callback(i: int) -> Union[Scatter, Volume]:
        return source.val(i * settings.speed).masked()

    scheduler = plot.auto_update(callback, settings.fps)

    fps_rec = []
    en_vals = dict(zip(((s.n, s.l, s.m) for s in atom.specs), (s.energy_func().ev_val() for s in states)))
    def on_step(i: int) -> None:
        nonlocal scheduler
        nonlocal fps_rec

        fps = scheduler.fps
        if fps > 0:
            fps_rec.append(fps)
            if len(fps_rec) > settings.fps:
                fps_rec.pop(0)

        fps_avg = sum(fps_rec) / len(fps_rec) if fps_rec else 0.0

        nonlocal en_vals
        plot.set_hud(
            f"speed:{' ' * 12}{settings.speed:.3g}\n"
            + f"fps:{' ' * 14}{fps_avg:.3g}\nspec:\n"
            + "\n".join(
                f"{' ' * 5}({s.n}, {s.l}, {s.m}):\n"
                f"{' ' * 7}en: {en_vals[(s.n, s.l, s.m)]: .6g} eV"
                for s in atom.specs
            )
        )

    scheduler.stepOccurred.connect(on_step)

    return plot, scheduler

if __name__ == "__main__":
    app = QApplication(sys.argv)
    res = main()
    sys.exit(app.exec())