from __future__ import annotations
from typing import Tuple, Union, Literal
from dataclasses import dataclass
import sys

from .ntypes import interpolation_t, ColormapT, SphDims
from .model import StateSpec, State, Atom, AtomPlotter
from .plot import *
from src.scheduler import *
from .interval import *

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QCheckBox, QPushButton, QFormLayout, QLineEdit, QLabel, QMessageBox, QSlider, QHBoxLayout, QScrollArea, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QCheckBox, QPushButton, QFormLayout, QLineEdit, QLabel, QMessageBox


@dataclass
class Settings:
    interactive: bool = True
    fps: int = 30
    speed: float = 1
    speed: float = 60.0
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_colormap: ColormapT = 'plasma'
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

class StateRow(QWidget):
    def __init__(self, parent_layout: QVBoxLayout, index: int, remove_callback: Callable):
        super().__init__()
        self.layout_ref = parent_layout
        self.remove_callback = remove_callback

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(row_layout)

        self.input_n = QLineEdit("1")
        self.input_l = QLineEdit("0")
        self.input_m = QLineEdit("0")

        for inp in [self.input_n, self.input_l, self.input_m]:
            inp.setFixedWidth(50)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_remove = QPushButton("X")
        self.btn_remove.setFixedWidth(30)
        self.btn_remove.setStyleSheet("color: red; font-weight: bold;")
        self.btn_remove.clicked.connect(self.remove_self)

        row_layout.addWidget(QLabel(f"State:"))
        row_layout.addWidget(QLabel("n="))
        row_layout.addWidget(self.input_n)
        row_layout.addWidget(QLabel("l="))
        row_layout.addWidget(self.input_l)
        row_layout.addWidget(QLabel("m="))
        row_layout.addWidget(self.input_m)
        row_layout.addWidget(self.btn_remove)

    def remove_self(self):
        self.remove_callback(self)
        self.setParent(None)
        self.deleteLater()

    def get_values(self) -> Tuple[int, int, int]:
        try:
            return int(self.input_n.text()), int(self.input_l.text()), int(self.input_m.text())
        except ValueError:
            raise ValueError("All quantum numbers must be integers.")


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, width=60, height=28, bg_color="#777", circle_color="#DDD", active_color="#00BCff"):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300)  # Animation speed in ms

        self.setText("")

        self.stateChanged.connect(self.start_transition)

    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_transition(self, state):
        self.animation.stop()
        if state:
            self.animation.setEndValue(self.width() - self.height() + 3)
        else:
            self.animation.setEndValue(3)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_color = QColor(self._active_color) if self.isChecked() else QColor(self._bg_color)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        p.setBrush(QColor(self._circle_color))

        p.drawEllipse(QRectF(self._circle_position, 3, self.height() - 6, self.height() - 6))
        p.end()

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu")
        self.resize(450, 400)

        self.current_plot = None
        self.current_interval = None
        self.superposition_rows = []

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.Dstate(), "Discrete state")
        self.tabs.addTab(self.Superposition(), "Superposition")
        main_layout.addWidget(self.tabs)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chk_volume = ToggleSwitch()

        lbl_scatter = QLabel("Scatter")
        lbl_volume = QLabel("Volume")

        font = QFont()
        font.setBold(True)
        lbl_scatter.setFont(font)
        lbl_volume.setFont(font)

        switch_layout.addWidget(lbl_scatter)
        switch_layout.addWidget(self.chk_volume)
        switch_layout.addWidget(lbl_volume)

        main_layout.addLayout(switch_layout)

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
        main_tab_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.states_container = QWidget()
        self.states_layout = QVBoxLayout()
        self.states_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.states_container.setLayout(self.states_layout)

        scroll.setWidget(self.states_container)
        main_tab_layout.addWidget(scroll)

        self.btn_add_state = QPushButton("+ Add State")
        self.btn_add_state.clicked.connect(self.add_state_row)
        main_tab_layout.addWidget(self.btn_add_state)

        self.add_state_row(defaults=(3, 2, 0))
        self.add_state_row(defaults=(2, 1, 0))

        Tab2.setLayout(main_tab_layout)
        return Tab2

    def add_state_row(self, defaults=None):
        row = StateRow(self.states_layout, len(self.superposition_rows), self.remove_state_row)
        if defaults:
            row.input_n.setText(str(defaults[0]))
            row.input_l.setText(str(defaults[1]))
            row.input_m.setText(str(defaults[2]))

        self.states_layout.addWidget(row)
        self.superposition_rows.append(row)

    def remove_state_row(self, row_object):
        if row_object in self.superposition_rows:
            self.superposition_rows.remove(row_object)

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
                states_list = []

                if not self.superposition_rows:
                    raise ValueError("Please add at least one state for superposition.")

                for row in self.superposition_rows:
                    n, l, m = row.get_values()
                    states_list.append(State(StateSpec(n, l, m)))

                atom = Atom(*states_list)

            settings = Settings()
            settings.plot_type = 'VolumePlot' if self.chk_volume.isChecked() else 'ScatterPlot'
            settings.interactive = True

            if self.current_interval is not None:
                try:
                    self.current_interval.stop()
                except RuntimeError:
                    pass
                self.current_interval = None

            if self.current_plot is not None:
                try:
                    if hasattr(self.current_plot, '_view'):
                        self.current_plot._view.hide()

                    self.current_plot.close()
                except:
                    pass
                self.current_plot = None

                QApplication.processEvents()

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