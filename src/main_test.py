from __future__ import annotations
from typing import Tuple, Union, Callable, Literal, Optional, Any
from dataclasses import dataclass
import sys

from .ntypes import interpolation_t, colormap_t, SphDims
from .model import StateSpec, State, Atom, AtomPlotter
from .plot import *
from .interval import *

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QCheckBox, QPushButton, QFormLayout, QLineEdit, QLabel, QMessageBox, QSlider
from PyQt6.QtCore import Qt



@dataclass
class Settings:
    interactive: bool = True
    fps: int = 30
    speed: float = 0.0001
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_colormap: colormap_t = 'plasma'
    plot_interpolation: interpolation_t = 'nearest'

def launch_custom_plot(atom: Atom, settings: Settings) -> Tuple[Union[ScatterPlotWindow, VolumePlotWindow], Optional[Interval]]:

    plotter = AtomPlotter(atom, SphDims(100, 100))

    plot_spec: PlotWindowSpec = PlotWindowSpec(
        title="Electron cloud of a hydrogen atom",
        cmap_name=settings.plot_colormap
    )

    plot = None

    if settings.plot_type == 'ScatterPlot':
        plot = ScatterPlotWindow(plot_spec)
        plot.draw(plotter.cart_scatter(0).masked())
    elif settings.plot_type == 'VolumePlot':
        plot = VolumePlotWindow(plot_spec)
        plot.draw(plotter.cart_grid(0, settings.plot_interpolation))
    else:
        raise ValueError(f"Unknown value of settings.plot_type: {settings.plot_type}")

    plot.show()

    interval: Optional[Interval] = None
    if settings.interactive:
        dt = 1.0 / settings.fps

        if settings.plot_type == 'ScatterPlot':
            callback = lambda i: plotter.cart_scatter(i * settings.speed * dt).masked()
        else:
            callback = lambda j: plotter.cart_grid(j * settings.speed * dt, settings.plot_interpolation)

        interval = plot.auto_update(callback, dt)
        interval.start()

    return plot, interval

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu")
        self.resize(405, 160)

        self.current_plot = None
        self.current_interval = None

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.Dstate(), "Discrete state")
        self.tabs.addTab(self.Superposition(), "Superposition of two states")
        main_layout.addWidget(self.tabs)

        self.chk_volume = QCheckBox("Volume Show Plot")
        main_layout.addWidget(self.chk_volume)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.clicked.connect(self.process_inputs)
        main_layout.addWidget(self.btn_apply)

    def Dstate(self):
        Tab1 = QWidget()
        layout = QFormLayout()

        self.input_n = QLineEdit()
        self.input_l = QLineEdit()
        self.input_m = QLineEdit()

        self.input_n.setText("1")
        self.input_l.setText("0")
        self.input_m.setText("0")

        layout.addRow(QLabel("n"), self.input_n)
        layout.addRow(QLabel("l"), self.input_l)
        layout.addRow(QLabel("m"), self.input_m)
        Tab1.setLayout(layout)

        return Tab1

    def Superposition(self):
        Tab2 = QWidget()
        layout = QFormLayout()

        self.input_n1 = QLineEdit()
        self.input_l1 = QLineEdit()
        self.input_m1 = QLineEdit()

        self.input_n2 = QLineEdit()
        self.input_l2 = QLineEdit()
        self.input_m2 = QLineEdit()

        self.input_n1.setText("3")
        self.input_l1.setText("2")
        self.input_m1.setText("0")
        self.input_n2.setText("2")
        self.input_l2.setText("1")
        self.input_m2.setText("0")

        layout.addRow(QLabel("n1"), self.input_n1)
        layout.addRow(QLabel("l1"), self.input_l1)
        layout.addRow(QLabel("m1"), self.input_m1)
        layout.addRow(QLabel("n2"), self.input_n2)
        layout.addRow(QLabel("l2"), self.input_l2)
        layout.addRow(QLabel("m2"), self.input_m2)

        Tab2.setLayout(layout)
        return Tab2

    def process_inputs(self):
        try:
            current_tab_index = self.tabs.currentIndex()
            atom = None

            if current_tab_index == 0:
                n = int(self.input_n.text())
                l = int(self.input_l.text())
                m = int(self.input_m.text())

                atom = Atom(State(StateSpec(n, l, m)))

            elif current_tab_index == 1:
                n1 = int(self.input_n1.text())
                l1 = int(self.input_l1.text())
                m1 = int(self.input_m1.text())

                n2 = int(self.input_n2.text())
                l2 = int(self.input_l2.text())
                m2 = int(self.input_m2.text())

                atom = Atom(State(StateSpec(n1, l1, m1)), State(StateSpec(n2, l2, m2)))

            settings = Settings()
            settings.plot_type = 'VolumePlot' if self.chk_volume.isChecked() else 'ScatterPlot'
            settings.interactive = True

            if self.current_plot:
                try:
                    self.current_plot.close()
                except:
                    pass

            self.current_plot, self.current_interval = launch_custom_plot(atom, settings)

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input values: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())