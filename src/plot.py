import matplotlib.pyplot as plt
import pyvista as pv

class Plot:
    def __init__(self):
        self.plotter = pv.Plotter()
        self.plotter.background_color = "black"
        self.plotter.window_size = (1920, 720)
        return



