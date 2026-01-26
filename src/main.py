from __future__ import annotations

# ==========================================
#               IMPORTY
# ==========================================

# --- Biblioteki standardowe ---
import sys
import traceback
from dataclasses import dataclass
from typing import (
    Tuple, Union, Literal, Callable, Optional
)

# --- Matematyczne ---
import numpy as np

# --- Wizualizacja i wykres ---
import colorcet as cc
import pyqtgraph as pg

# --- PyQt6 GUI ---
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRectF
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QImage, QIntValidator
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QCheckBox, QPushButton, QLineEdit, QComboBox,
    QLabel, QMessageBox, QSlider, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QFileDialog
)

# --- Nasze moduły ---
from .ntypes import ColormapTypeT, SphDims, Scatter, Volume
from .model import StateSpec, State, Atom, Plotter
from .plot import Window, WindowSpec, ScatterWindow, VolumeWindow
from .scheduler import *

# ==========================================
#               STYL GUI
# ==========================================

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
    font-size: 15px;
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

# ==========================================
#           Konfiguracje
# ==========================================

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

CUSTOM_MAPS = {}


def create_pg_cmap(hex_list):
    colors = []
    for h in hex_list:
        c = QColor(h)
        colors.append([c.red(), c.green(), c.blue(), 255])

    colors = np.array(colors, dtype=np.uint8)
    positions = np.linspace(0.0, 1.0, len(colors))
    return pg.ColorMap(positions, colors)


# --- Rejestracja modułów kolorystycznych ---
favorites = {
    'cc_fire': cc.fire,
    'cc_glasbey': cc.glasbey,
    'cc_bmy': cc.bmy,
    'cc_coolwarm': cc.coolwarm,
    'cc_rainbow': cc.rainbow,
    'cc_kbc': cc.kbc
}

for name, hex_data in favorites.items():
    CUSTOM_MAPS[name] = create_pg_cmap(hex_data)

_original_pg_get = pg.colormap.get


def patched_get_colormap(name, *args, **kwargs):
    if name in CUSTOM_MAPS:
        return CUSTOM_MAPS[name]
    return _original_pg_get(name, *args, **kwargs)


pg.colormap.get = patched_get_colormap


@dataclass
class Settings:
    interactive: bool = True
    fps: int = 20
    speed: float = 1.0
    plot_type: Literal['ScatterPlot', 'VolumePlot'] = 'ScatterPlot'
    plot_dims: SphDims = SphDims(100, 100)
    plot_colormap: ColormapTypeT = 'plasma'
    show_hud: bool = True
    show_colorbar: bool = True


settings: Settings = Settings()


# ==========================================
#           Rdzenna logika wykresu
# ==========================================

def launch_custom_plot(
        atom: Atom,
        settings: Settings,
        rows: list[StateRow]
) -> Tuple[Union[ScatterWindow, VolumeWindow], Optional[Scheduler]]:
    # 1. Specyfikacje
    plot_spec: WindowSpec = WindowSpec(
        title = "Chmura elektronowa atomu wodoru",
        cmap_name = settings.plot_colormap,
        show_hud = True,
        show_colorbar = True
    )
    plotter = Plotter(atom, settings.plot_dims)

    # 2. Typ wykresu
    if settings.plot_type == 'ScatterPlot':
        source = plotter.scatter()
        plot = ScatterWindow(plot_spec)
    elif settings.plot_type == 'VolumePlot':
        source = plotter.volume()
        plot = VolumeWindow(plot_spec)
    else:
        raise ValueError(f"Unknown value: {settings.plot_type}")

    # 3. Pierwotny zarys
    plot.draw(source.val().masked())
    plot.showMaximized()

    if plot._view.colorbar:
        plot._view.colorbar.setVisible(settings.show_colorbar)

    # 4. Ineraktywny harmonogram
    scheduler: Optional[Scheduler] = None

    if settings.interactive:
        sim_time = 0.0

        dt = 1.0 / settings.fps

        def callback(i: int) -> Union[Scatter, Volume]:
            nonlocal sim_time

            sim_time += dt * settings.speed

            return source.val(sim_time).masked()
        scheduler = plot.auto_update(callback, settings.fps)

        # HUD
        en_vals = {}
        for row in rows:
            try:
                n, l, m = row.get_values()
                temp_state = State(StateSpec(n, l, m))
                en_vals[(n, l, m)] = temp_state.energy_func().ev_val()
            except Exception:
                en_vals[(n, l, m)] = 0.0

        fps_rec = []

        def on_step(i: int) -> None:
            nonlocal fps_rec

            # Obliczenia FPS
            current_fps = scheduler.fps if scheduler else 0
            fps_rec.append(current_fps)
            if len(fps_rec) > settings.fps:
                fps_rec.pop(0)
            fps_avg = sum(fps_rec) / len(fps_rec) if fps_rec else 0.0

            # Konstrukcja HUD
            if settings.show_hud:
                hud_text = (
                    f"Speed: {settings.speed:>10.2f}x\n"
                    f"FPS:   {fps_avg:>10.1f}\n"
                    f"Spec:\n"
                )

                for row in rows:
                    try:
                        n, l, m = row.get_values()
                        energy = en_vals.get((n, l, m), 0.0)
                        hud_text += f"  ({n}, {l}, {m}): {energy:.4f} eV\n"
                    except:
                        continue

                plot.set_hud(hud_text)
            else:
                plot.set_hud("")

        scheduler.stepOccurred.connect(on_step)

    def toggle_colorbar(visible: bool):
        if plot._view.colorbar:
            plot._view.colorbar.setVisible(visible)

    plot.toggle_colorbar = toggle_colorbar

    return plot, scheduler


# =======================================================
#           KOMPONENTY INTERFEJSU UŻYTKOWNIKA
# =======================================================

class StateRow(QWidget):
    def __init__(self, parent_layout: QVBoxLayout, index: int, remove_callback: Callable):
        super().__init__()
        self.layout_ref = parent_layout
        self.remove_callback = remove_callback

        # --- Rama kart ---
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

        # --- Dane wejściowe ---
        self.input_n = QLineEdit("1")
        self.input_l = QLineEdit("0")
        self.input_m = QLineEdit("0")

        for inp in [self.input_n, self.input_l, self.input_m]:
            inp.setFixedWidth(50)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Przyciski i etykiety ---
        self.btn_remove = QPushButton("X")
        self.btn_remove.setObjectName("DestructiveButton")
        self.btn_remove.setFixedWidth(36)
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.clicked.connect(self.remove_self)

        lbl_title = QLabel(f"Orbital {index + 1}")
        lbl_title.setStyleSheet("color: #00BCff; font-weight: bold;")

        # --- Połączenie układu ---
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

    def energy_state(self) -> Tuple[int, int, int]:
        n, l, m = self.get_values
        return n, l, m


class ToggleSwitch(QCheckBox):
    def __init__(
            self,
            parent=None,
            width=50,
            height=26,
            bg_color="#4e5254",
            circle_color="#ffffff",
            active_color="#00BCff"
    ):
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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu")
        self.resize(500, 550)

        # --- Inicjalizacja danych ---
        self.current_atom = None

        self.settings = Settings()
        self.settings.speed = 2.0
        self.settings.fps = 20
        self.settings.interactive = True
        self.settings.plot_colormap = 'plasma'
        self.settings.show_hud = True
        self.settings.show_colorbar = True
        self.settings.plot_dims = SphDims(100,100)

        self.plot_cache = {
            'ScatterPlot': {'window': None, 'scheduler': None},
            'VolumePlot': {'window': None, 'scheduler': None}
        }

        self.window_settings = QPushButton("Zrzut ekranu")
        self.window_settings.setMinimumHeight(40)
        self.window_settings.clicked.connect(self.take_snapshot)
        self.window_settings.setFixedWidth(110)

        self.current_plot = None
        self.current_Scheduler = None
        self.superposition_rows = []

        # --- Inicjalizacja interfejsu użytkownika ---
        self.setStyleSheet(DARK_STYLESHEET)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.window_settings, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(main_layout)

        # --- Zakładki ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self.Superposition(), "Kreator orbitali")
        self.tabs.addTab(self.Dstate(), "Ustawienia")
        main_layout.addWidget(self.tabs)

        # --- Dolny pasek kontrolny ---
        bottom_container = QFrame()
        bottom_container.setStyleSheet("background: #3c3f41; border-radius: 8px;")
        bottom_layout = QVBoxLayout()
        bottom_container.setLayout(bottom_layout)

        # --- Przycisk "Zastosuj" ---
        self.btn_apply = QPushButton("Zastosuj")
        self.btn_apply.setObjectName("PrimaryButton")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self.process_inputs)

        main_layout.addWidget(self.btn_apply)

    # --- Metody konfiguracji ---

    def hud_check(self, state):
        self.settings.show_hud = (state == 2)

    def colorbar_check(self, state):
        is_checked = (state == 2)
        self.settings.show_colorbar = is_checked

        target_type = self.settings.plot_type
        cache = self.plot_cache[target_type]

        if cache['window'] is not None:
            if hasattr(cache['window'], 'toggle_colorbar'):
                cache['window'].toggle_colorbar(is_checked)

    def update_colormap(self, text):
        self.settings.plot_colormap = text
        print(f"Colormap changed to: {text}")

    def update_speed(self, value):
        new_speed = float(value) / 10.0
        label_speed = new_speed /10
        self.settings.speed = new_speed
        self.lbl_speed.setText(f"Szybkość animacji: {label_speed:.2f}x")

    def take_snapshot(self):
        active_window = None

        for key, cache in self.plot_cache.items():
            win = cache['window']
            if win is not None and win._view.isVisible():
                active_window = win
                break

        if active_window is None:
            QMessageBox.warning(self, "Błąd", "Nie wykryto aktywnego okna z wykresem.")
            return

        try:
            img_array = active_window.snapshot()

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Zapisz zrzut ekranu",
                "snapshot.png",
                "Images (*.png *.jpg *.bmp)"
            )

            if file_path:
                height, width, channels = img_array.shape
                bytes_per_line = channels * width

                if not img_array.flags['C_CONTIGUOUS']:
                    img_array = np.ascontiguousarray(img_array)

                q_img = QImage(
                    img_array.data,
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format.Format_RGBA8888
                )

                if q_img.save(file_path):
                    QMessageBox.information(self, "Sukces", f"Zapisano zrzut w:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Błąd", "Nie udało się zapisać pliku.")

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd:\n{e}")

    # --- Tworzenie interfejsu użytkownika ---

    def Dstate(self):
        Tab1 = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_label = QLabel("Dodatkowe ustawienia")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")

        form_layout = QFormLayout()

        self.box_cmap = QComboBox()
        available_maps = [
            'plasma', 'viridis', 'inferno', 'magma', 'cividis', 'grey',
            'cc_fire', 'cc_glasbey', 'cc_bmy', 'cc_coolwarm', 'cc_rainbow', 'cc_kbc'
        ]
        self.box_cmap.addItems(available_maps)
        self.box_cmap.currentTextChanged.connect(self.update_colormap)
        self.box_cmap.setFixedWidth(200)
        form_layout.addRow("Kolor mapy:", self.box_cmap)

        self.hud = QCheckBox("Pokaż HUD")
        self.hud.setChecked(self.settings.show_hud)
        self.hud.stateChanged.connect(self.hud_check)
        self.hud.setCursor(Qt.CursorShape.PointingHandCursor)

        self.colorbar = QCheckBox("Colorbar")
        self.colorbar.setChecked(self.settings.show_colorbar)
        self.colorbar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.colorbar.stateChanged.connect(self.colorbar_check)

        fps_layout = QHBoxLayout()
        self.input_fps = QLineEdit("20")
        validator = QIntValidator(5, 120)
        self.input_fps.setValidator(validator)
        self.input_fps.setFixedWidth(60)

        fps_layout.addWidget(self.input_fps)
        fps_layout.addStretch()

        form_layout.addRow("FPS:", fps_layout)

        dims_layout = QHBoxLayout()
        self.input_dim_x = QLineEdit("100")
        validator = QIntValidator(10, 1000)
        self.input_dim_x.setValidator(validator)
        self.input_dim_x.setFixedWidth(60)

        dims_layout.addWidget(QLabel(""))
        dims_layout.addWidget(self.input_dim_x)
        dims_layout.addStretch()

        form_layout.addRow("Wymiary przestrzeni:", dims_layout)

        layout.addWidget(info_label)
        layout.addLayout(form_layout)
        layout.addWidget(self.hud)
        layout.addWidget(self.colorbar)
        layout.addStretch()

        self.lbl_speed = QLabel(f"Szybkość animacji: {self.settings.speed / 10:.2f}x")
        self.lbl_speed.setStyleSheet("font-weight: bold; color: #00BCff;")
        layout.addWidget(self.lbl_speed)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10,500)
        self.speed_slider.setValue(int(self.settings.speed*10))
        self.speed_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speed_slider.valueChanged.connect(self.update_speed)

        self.speed_slider.setTickInterval(25)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        layout.addWidget(self.speed_slider)
        layout.addStretch()

        self.chk_volume = ToggleSwitch()

        lbl_scatter = QLabel("Scatter")
        lbl_volume = QLabel("Volume")

        font = QFont()
        font.setBold(True)
        lbl_scatter.setFont(font)
        lbl_volume.setFont(font)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        switch_layout.addWidget(lbl_scatter)
        switch_layout.addWidget(self.chk_volume)
        switch_layout.addWidget(lbl_volume)

        layout.addLayout(switch_layout)

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

        # Default states
        self.add_state_row(defaults=(3, 2, 0))
        self.add_state_row(defaults=(2, 1, 0))

        Tab2.setLayout(main_tab_layout)
        return Tab2

    # --- Metody logiki ---

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
            # --- Zebranie danych stanu ---
            states_list = []
            if not self.superposition_rows:
                raise ValueError("Proszę dodać conajmniej jeden stan.")

            for row in self.superposition_rows:
                n, l, m = row.get_values()
                states_list.append(State(StateSpec(n, l, m)))
            self.current_atom = Atom(*states_list)

            atom_to_plot = self.current_atom

            # --- Określenie typu wykresu ---
            target_type = 'VolumePlot' if self.chk_volume.isChecked() else 'ScatterPlot'
            other_type = 'ScatterPlot' if target_type == 'VolumePlot' else 'VolumePlot'

            self.settings.plot_type = target_type
            self.settings.interactive = True

            try:
                dim_x = int(self.input_dim_x.text())
                self.settings.plot_dims = SphDims(dim_x, dim_x)
            except ValueError:
                raise ValueError("Rozdzielczość musi być liczbą całkowitą.")

            try:
                fps_val = int(self.input_fps.text())
                self.settings.fps = fps_val
            except ValueError:
                raise ValueError("FPS musi być liczbą całkowitą.")

            # --- Niszczenie starego wykresu ---
            def destroy_window(cache_entry):
                if cache_entry['window'] is not None:
                    try:
                        cache_entry['window'].abort()
                    except Exception:
                        pass
                    cache_entry['window'] = None
                    cache_entry['scheduler'] = None

            destroy_window(self.plot_cache[other_type])

            target_cache = self.plot_cache[target_type]
            destroy_window(target_cache)

            # --- Inicjalizacja wykresu ---
            plot, scheduler = launch_custom_plot(
                atom_to_plot,
                self.settings,
                self.superposition_rows
            )

            target_cache['window'] = plot
            target_cache['scheduler'] = scheduler

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Nieprawidłowe dane wejściowe: {e}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Nastąpił nieoczekiwany błąd: {e}")
            print(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())