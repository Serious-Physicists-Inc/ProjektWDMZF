import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

class Plot:
    def __init__(self):
        self.plotter = pv.Plotter()
        self.plotter.background_color = "black"
        self.plotter.window_size = (1920, 720)
        return
    def draw(self, grid: np.array) -> None:
        plotter.add_mesh(chmura,
                         scalars="Prawd",
                         cmap="plasma",
                         point_size=5.0,
                         render_points_as_spheres=True,
                         opacity="linear",
                         show_scalar_bar=False)




