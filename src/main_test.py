from __future__ import annotations
from typing import Tuple, Union, Literal, Callable, Optional
from dataclasses import dataclass
import sys

from .ntypes import ColormapT, SphDims, Scatter, Volume
from .model import StateSpec, State, Atom, Plotter
from .plot import *
from .scheduler import *

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QCheckBox, QPushButton, QFormLayout, QLineEdit, QLabel, QMessageBox, QSlider, QHBoxLayout, QScrollArea, QFrame, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QIcon, QColorConstants

import traceback

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #2b2d30;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

QLabel {
    background-color: transparent;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #3c3f41;
    border-radius: 4px;
    background: #2b2d30;
}
QTabBar::tab {
    background: #3c3f41;
    color: #bbb;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #4e5254;
    color: white;
    font-weight: bold;
    border-bottom: 2px solid #00BCff;
}

/* Inputs */
QLineEdit {
    background-color: #1e1f22;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
    color: white;
    font-weight: bold;
}
QLineEdit:focus {
    border: 1px solid #00BCff;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* Buttons */
QPushButton {
    background-color: #36393d;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 6px 12px;
    color: white;
}
QPushButton:hover {
    background-color: #4e5254;
}
QPushButton#PrimaryButton {
    background-color: #00BCff;
    border: none;
    color: black;
    font-weight: bold;
    font-size: 15px;
    padding: 10px;
}
QPushButton#PrimaryButton:hover {
    background-color: #33c9ff;
}
QPushButton#DestructiveButton {
    background-color: transparent;
    color: #ff6b6b;
    border: 1px solid #ff6b6b;
    font-weight: bold;
}
QPushButton#DestructiveButton:hover {
    background-color: #ff6b6b;
    color: white;
}

/* Cards */
QFrame#StateCard {
    background-color: #3c3f41;
    border-radius: 8px;
    border: 1px solid #4e5254;
}
"""

@dataclass
class Settings:
    interactive: bool = True
    fps: int = 20
    speed: float = 1
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_colormap: ColormapT = 'plasma'

settings: Settings = Settings()

def launch_custom_plot(atom: Atom, settings: Settings) -> Tuple[Union[ScatterPlotWindow, VolumePlotWindow], Optional[Scheduler]]:
    plot_spec: PlotWindowSpec = PlotWindowSpec(
        title="Chmura elektronowa atomu wodoru",
        cmap_name=settings.plot_colormap
    )

    plotter = Plotter(atom, SphDims(100, 100))
    if settings.plot_type == 'ScatterPlot':
        source = plotter.scatter()
        plot = ScatterPlotWindow(plot_spec)
    elif settings.plot_type == 'VolumePlot':
        source = plotter.volume()
        plot = VolumePlotWindow(plot_spec)
    else:
        raise ValueError(f"Unknown value of settings.plot_type: {settings.plot_type}")
    plot.draw(source.val().masked())
    plot.show()

    scheduler: Optional[Scheduler] = None
    if settings.interactive:
        def callback(i: int) -> Union[Scatter, Volume]:
            return source.val(i * settings.speed / settings.fps).masked()

        scheduler = plot.auto_update(callback, settings.fps)

        fps_rec = []
        def on_step(i: int) -> None:
            nonlocal scheduler
            nonlocal fps_rec

            fps = scheduler.fps
            if fps > 0:
                fps_rec.append(fps)
                if len(fps_rec) > settings.fps:
                    fps_rec.pop(0)

        scheduler.stepOccurred.connect(on_step)

    return plot, scheduler

class StateRow(QWidget):
    def __init__(self, parent_layout: QVBoxLayout, index: int, remove_callback: Callable):
        super().__init__()
        self.layout_ref = parent_layout
        self.remove_callback = remove_callback

        self.card_frame = QFrame()
        self.card_frame.setObjectName("StateCard")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.card_frame.setGraphicsEffect(shadow)

        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(10)
        self.card_frame.setLayout(card_layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.card_frame)
        self.setLayout(main_layout)

        self.input_n = QLineEdit("1")
        self.input_l = QLineEdit("0")
        self.input_m = QLineEdit("0")

        for inp in [self.input_n, self.input_l, self.input_m]:
            inp.setFixedWidth(50)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_remove = QPushButton("✕")
        self.btn_remove.setObjectName("DestructiveButton")
        self.btn_remove.setFixedWidth(30)
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.clicked.connect(self.remove_self)

        lbl_title = QLabel(f"Orbital {index + 1}")
        lbl_title.setStyleSheet("color: #00BCff; font-weight: bold;")

        card_layout.addWidget(lbl_title)
        card_layout.addStretch()

        def make_lbl(html_text):
            l = QLabel(html_text)
            l.setStyleSheet("font-family: 'Times New Roman', serif; font-size: 19px; color: #ffffff;")
            return l

        card_layout.addWidget(make_lbl("<i>n</i> :"))
        card_layout.addWidget(self.input_n)
        card_layout.addWidget(make_lbl("ℓ :"))
        card_layout.addWidget(self.input_l)
        card_layout.addWidget(make_lbl("<i>m<sub>ℓ</sub></i> :"))
        card_layout.addWidget(self.input_m)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.btn_remove)

    def remove_self(self):
        self.remove_callback(self)
        self.setParent(None)
        self.deleteLater()

    def get_values(self) -> Tuple[int, int, int]:
        try:
            return int(self.input_n.text()), int(self.input_l.text()), int(self.input_m.text())
        except ValueError:
            raise ValueError("Wszystkie liczby kwantowe muszą być liczbami całkowitymi.")


class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, width=50, height=26, bg_color="#4e5254", circle_color="#ffffff", active_color="#00BCff"):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(250)

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

        radius = int(self.height() / 2)
        p.drawRoundedRect(0, 0, self.width(), self.height(), radius, radius)

        p.setBrush(QColor(self._circle_color))

        p.drawEllipse(QRectF(self._circle_position, 3, self.height() - 6, self.height() - 6))
        p.end()

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu")
        self.resize(500, 550)

        self.current_plot = None
        self.current_Scheduler = None
        self.superposition_rows = []

        self.setStyleSheet(DARK_STYLESHEET)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.Superposition(), "Kreator orbitali")
        self.tabs.addTab(self.Dstate(), "Ustawienia")
        main_layout.addWidget(self.tabs)

        bottom_container = QFrame()
        bottom_container.setStyleSheet("background: #3c3f41; border-radius: 8px;")
        bottom_layout = QVBoxLayout()
        bottom_container.setLayout(bottom_layout)

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

        self.btn_apply = QPushButton("Zastosuj")
        self.btn_apply.setObjectName("PrimaryButton")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_apply.clicked.connect(self.process_inputs)
        main_layout.addWidget(self.btn_apply)

    def Dstate(self):
        Tab1 = QWidget()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_label = QLabel("Dodatkowe ustawienia")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")

        self.window_settings = QPushButton("Zrzut ekranu")
        self.window_settings.setMinimumHeight(40)

        layout.addWidget(info_label)
        layout.addWidget(self.window_settings)
        layout.addStretch()

        Tab1.setLayout(layout)
        return Tab1

    def Superposition(self):
        Tab2 = QWidget()
        main_tab_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.states_container = QWidget()
        self.states_layout = QVBoxLayout()
        self.states_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.states_layout.setSpacing(10)
        self.states_container.setLayout(self.states_layout)

        scroll.setWidget(self.states_container)
        main_tab_layout.addWidget(scroll)

        self.btn_add_state = QPushButton("+ Dodaj stan")
        self.btn_add_state.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_state.clicked.connect(lambda: self.add_state_row())
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
                states_list = []

                if not self.superposition_rows:
                    raise ValueError("Proszę dodać conajmniej jeden stan.")

                for row in self.superposition_rows:
                    n, l, m = row.get_values()
                    states_list.append(State(StateSpec(n, l, m)))

                atom = Atom(*states_list)

            settings = Settings()
            settings.plot_type = 'VolumePlot' if self.chk_volume.isChecked() else 'ScatterPlot'
            settings.interactive = True

            if self.current_Scheduler is not None:
                try:
                    self.current_Scheduler.abort()
                except RuntimeError:
                    pass
                self.current_Scheduler = None

            if self.current_plot is not None:
                try:
                    if hasattr(self.current_plot, '_view'):
                        self.current_plot._view.hide()

                    self.current_plot.close()
                except:
                    pass
                self.current_plot = None

                QApplication.processEvents()

            self.current_plot, self.current_Scheduler = launch_custom_plot(atom, settings)

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Nieprawidłowe dane wejściowe: {e}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Nastąpił nieoczekiwany błąd: {e}")
            print(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())