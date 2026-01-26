from __future__ import annotations
import sys
import traceback
from typing import Union, Optional, List

from .stylesheet import stylesheet
from .row import Row
from .switch import ToggleSwitch
from .ntypes import ColormapTypeT, SphDims, Scatter, Volume
from .model import StateSpec, State, Atom, Plotter
from .plot import WindowSpec, ScatterWindow, VolumeWindow
from .scheduler import Scheduler

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QImage, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QCheckBox, QPushButton, QLineEdit, QComboBox,
    QLabel, QMessageBox, QSlider, QScrollArea, QFrame, QFileDialog)
import pyqtgraph as pg

QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

<<<<<<< Updated upstream
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


=======
>>>>>>> Stashed changes
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu")
        self.resize(500, 550)
<<<<<<< Updated upstream

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
=======
        self.setStyleSheet(stylesheet)
>>>>>>> Stashed changes
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.__atom: Optional[Atom] = None
        self.__plot: Optional[Union[ScatterWindow, VolumeWindow]] = None
        self.__scheduler: Optional[Scheduler] = None
        self.__rows: List[Row] = []

        self.__btn_snapshot = QPushButton("Zrzut ekranu")
        self.__btn_snapshot.setMinimumHeight(30)
        self.__btn_snapshot.setFixedWidth(110)
        self.__btn_snapshot.clicked.connect(self.take_snapshot)
        main_layout.addWidget(self.__btn_snapshot, alignment=Qt.AlignmentFlag.AlignRight)

        self.__tabs = QTabWidget()
        self.__tabs.addTab(self.__states_tab(), "Kreator orbitali")
        self.__tabs.addTab(self.__settings_tab(), "Ustawienia")
        main_layout.addWidget(self.__tabs)

        self.__btn_apply = QPushButton("Zastosuj")
        self.__btn_apply.setObjectName("PrimaryButton")
        self.__btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.__btn_apply.clicked.connect(self.__process)

<<<<<<< Updated upstream
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
=======
        main_layout.addWidget(self.__btn_apply)
    @property
    def fps(self) -> int:
        return int(self.__inp_fps.text())
    @property
    def speed(self) -> float:
        return self.__sld_speed.value() / 10.0
    @property
    def dim(self) -> int:
        return int(self.__inp_dim.text())
    @property
    def cmap_name(self) -> ColormapTypeT:
        return self.__box_cmap.currentText()
    @property
    def show_hud(self) -> bool:
        return self.__hud.isChecked()
    @property
    def show_colorbar(self) -> bool:
        return self.__colorbar.isChecked()
    @property
    def plot_type(self) -> str:
        return 'volume' if self.__chk_vol.isChecked() else 'scatter'
    def take_snapshot(self) -> None:
        if self.__plot is None:
>>>>>>> Stashed changes
            QMessageBox.warning(self, "Błąd", "Nie wykryto aktywnego okna z wykresem.")
            return

        try:
            img_array = self.__plot.snapshot()
            file_path, _ = QFileDialog.getSaveFileName(self,"Zapisz zrzut ekranu","snapshot.png","PNG Image (*.png);;JPEG Image (*.jpg);;Bitmap (*.bmp)")

            if file_path:
                height, width, channels = img_array.shape
                qimg = QImage(img_array.tobytes(), width, height, channels * width, QImage.Format.Format_RGBA8888)

                if qimg.save(file_path):
                    QMessageBox.information(self, "Sukces", f"Zrzut wykresu zapisano do pliku:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Błąd", "Zapis do pliku nie powiódł się")

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd:\n{e}")

    def __settings_tab(self):
        Tab1 = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_label = QLabel("Dodatkowe ustawienia")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 12px;")

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(12)

        label_width = 260

        def make_label(text):
            lbl = QLabel(text)
            lbl.setFixedWidth(label_width)
            return lbl

        self.__box_cmap = QComboBox()
        self.__box_cmap.addItems(sorted(pg.colormap.listMaps()))
        self.__box_cmap.setCurrentText("plasma")
        self.__box_cmap.setMinimumWidth(220)

        form_layout.addRow(make_label("Skala kolorów:"), self.__box_cmap)

        self.__inp_fps = QLineEdit("20")
        self.__inp_fps.setValidator(QIntValidator(5, 120))
        self.__inp_fps.setFixedWidth(80)

        form_layout.addRow(make_label("Ilość klatek na sekundę:"), self.__inp_fps)

        self.__inp_dim = QLineEdit("100")
        self.__inp_dim.setValidator(QIntValidator(20, 1000))
        self.__inp_dim.setFixedWidth(80)

        form_layout.addRow(make_label("Rozmiar siatki przestrzennej:"), self.__inp_dim)

<<<<<<< Updated upstream
        form_layout.addRow("Wymiary przestrzeni:", dims_layout)
=======
        self.__hud = QCheckBox()
        self.__hud.setChecked(True)

        form_layout.addRow(make_label("Pokaż HUD:"), self.__hud)

        self.__colorbar = QCheckBox()
        self.__colorbar.setChecked(True)

        form_layout.addRow(make_label("Colorbar:"), self.__colorbar)
>>>>>>> Stashed changes

        layout.addWidget(info_label)
        layout.addLayout(form_layout)
        layout.addSpacing(25)

<<<<<<< Updated upstream
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
=======
        speed_layout = QHBoxLayout()

        lbl_speed_title = QLabel("Szybkość animacji:")
        lbl_speed_title.setStyleSheet("font-weight: bold; color: #00BCff;")

        self.__lbl_speed_value = QLabel("0.1")
        self.__lbl_speed_value.setStyleSheet("font-weight: bold; color: #00BCff;")
>>>>>>> Stashed changes

        lbl_speed_unit = QLabel("x")
        lbl_speed_unit.setStyleSheet("font-weight: bold; color: #00BCff;")

        speed_layout.addWidget(lbl_speed_title)
        speed_layout.addSpacing(8)
        speed_layout.addWidget(self.__lbl_speed_value)
        speed_layout.addWidget(lbl_speed_unit)
        speed_layout.addStretch()

        layout.addLayout(speed_layout)

        self.__sld_speed = QSlider(Qt.Orientation.Horizontal)
        self.__sld_speed.setMinimum(1)
        self.__sld_speed.setMaximum(20)
        self.__sld_speed.setValue(1)
        self.__sld_speed.valueChanged.connect(
            lambda v: self.__lbl_speed_value.setText(f"{v / 10:.1f}")
        )

        layout.addWidget(self.__sld_speed)
        layout.addSpacing(30)

        self.__chk_vol = ToggleSwitch()

        lbl_scatter = QLabel("Scatter")
        lbl_volume = QLabel("Volume")

        font = QFont()
        font.setBold(True)
        lbl_scatter.setFont(font)
        lbl_volume.setFont(font)

        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        switch_layout.addWidget(lbl_scatter)
        switch_layout.addSpacing(10)
        switch_layout.addWidget(self.__chk_vol)
        switch_layout.addSpacing(10)
        switch_layout.addWidget(lbl_volume)

        layout.addLayout(switch_layout)

        Tab1.setLayout(layout)
        return Tab1
    def __states_tab(self) -> QWidget:
        Tab2 = QWidget()
        main_tab_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        states_container = QWidget()
        self.__states_layout = QVBoxLayout()
        self.__states_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        states_container.setLayout(self.__states_layout)

        scroll.setWidget(states_container)
        main_tab_layout.addWidget(scroll)

        self.__btn_add_state = QPushButton("+ Dodaj stan")
        self.__btn_add_state.clicked.connect(lambda: self.__add_row())
        main_tab_layout.addWidget(self.__btn_add_state)

        self.__add_row(defaults=(3,2,0))
        self.__add_row(defaults=(2,1,0))

        Tab2.setLayout(main_tab_layout)
        return Tab2
    def __add_row(self, defaults=None) -> None:
        row = Row(self.__states_layout)
        row.removeBtnClickOccurred.connect(lambda r=row: self.__remove_row(r))
        row.set_index(len(self.__rows))

        if defaults:
            row.n,row.l,row.m = defaults

        self.__states_layout.addWidget(row)
        self.__rows.append(row)
    def __remove_row(self, row_object: Row) -> None:
        if row_object in self.__rows:
            self.__rows.remove(row_object)

        row_object.setParent(None)
        row_object.deleteLater()

        for i,row in enumerate(self.__rows):
            row.set_index(i)
    def __process(self) -> None:
        try:
            states = []
            if not self.__rows:
                raise ValueError("Wymagane podanie przynajmniej jednego stanu")

            for row in self.__rows:
                states.append(State(StateSpec(row.n,row.l,row.m)))
            self.__atom = Atom(*states)

            plot_spec: WindowSpec = WindowSpec(
                title="Chmura elektronowa atomu wodoru",
                cmap_name=self.cmap_name,
                show_hud=self.show_hud,
                show_colorbar=self.show_colorbar
            )

            plotter = Plotter(self.__atom,SphDims(self.dim,self.dim))

            if self.plot_type == 'volume':
                source = plotter.volume()
                self.__plot = VolumeWindow(plot_spec)
            else:
                source = plotter.scatter()
                self.__plot = ScatterWindow(plot_spec)

            self.__plot.draw(source.val().masked())
            self.__plot.show()

            def callback(i: int) -> Union[Scatter,Volume]:
                return source.val(i * self.speed).masked()

            if self.__scheduler is not None:
                self.__scheduler.abort()

            self.__scheduler = self.__plot.auto_update(callback,self.fps)

            fps_rec = []
            en_vals = dict(zip(((spec.n,spec.l,spec.m) for spec in self.__atom.specs),(state.energy_func().ev_val() for state in self.__atom.states)))

            def on_step(i: int) -> None:
                nonlocal fps_rec,en_vals

                current_fps = self.__scheduler.fps
                fps_rec.append(current_fps)
                if len(fps_rec) > self.fps:
                    fps_rec.pop(0)
                fps_avg = sum(fps_rec) / len(fps_rec) if fps_rec else 0.0

                if self.show_hud:
                    self.__plot.set_hud(
                        f"speed:{self.speed:>15.2f}\n"
                        f"fps:{fps_avg:>17.1f}\nspec:\n"
                        + "\n".join(
                            f"{' ' * 5}({s.n},{s.l},{s.m}):\n"
                            f"{' ' * 7}en: {en_vals[(s.n,s.l,s.m)]:.4f} eV"
                            for s in self.__atom.specs
                        )
                    )

            self.__scheduler.stepOccurred.connect(on_step)

        except ValueError as error:
            QMessageBox.warning(self,"Input Error",f"Nieprawidłowe dane wejściowe: {error}")
        except Exception as exception:
            traceback.print_exc()
            QMessageBox.critical(self,"Error",f"Nastąpił nieoczekiwany błąd: {exception}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())