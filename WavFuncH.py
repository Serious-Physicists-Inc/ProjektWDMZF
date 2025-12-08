import numpy as np
import matplotlib.pyplot as plt
pi = np.pi
from scipy.special import factorial as fact
from scipy.special import genlaguerre as Laguerre
from scipy.special import lpmv as Legendre
import pyvista as pv

n = int(input('Wprowadz glowna liczbe kwantowa'))
l = int(input('Wprowadz poboczna liczbe kwantowa'))
m = int(input('Wprowadz magnetyczna liczbe kwantowa'))

def przestrz(n, rozm_r=180, rozm_k=150):
    rmax =  10*n**2
    r = np.linspace(0, rmax, rozm_r)
    theta = np.linspace(0, np.pi, rozm_k)
    phi = np.linspace(0, 2*np.pi, rozm_k)

    R, Theta, Phi = np.meshgrid(r, theta, phi, indexing='ij')

    return R, Theta, Phi


def funkfal(R,Theta,Phi,n,l,m):
    a0 = 1.0

    if type(n) != int:
        raise TypeError('glowna liczba kwantowa musi byc liczba calkowita')
    elif n < 0:
        raise ValueError('wartosc glownej liczby kwantowej musi byc wieksza od 0')
    elif type(l) != int:
        raise TypeError('poboczna liczba kwantowa musi byc liczba calkowita')
    elif l >= n:
        raise ValueError('wartosc pobocznej liczby kwantowej musi byc mniejsza od n')
    elif type(m) != int:
        raise TypeError('liczba magnetyczna musi byc liczba calkowita')
    elif m < -l or m > l:
        raise ValueError('modul liczby magnetycznej nie moze byc wiekszy od l')

    P = np.asarray(Legendre(abs(m),l,np.cos(Theta)), dtype=complex)

    kat = (-1)**abs(m)*np.sqrt(((2*l+1)*fact(l-abs(m)))/(4*pi*fact(l+abs(m))))*P*np.exp(1j*abs(m)*Phi)

    L = np.asarray(Laguerre(n-l-1,2*l+1)(2*R/(n*a0)), dtype=float)

    rad = R**l*(2/(n*a0))**(l+1)*L*np.exp(-R/(n*a0))

    Psi = rad * kat

    return np.asarray(Psi, dtype=complex)

def chmuraprawd(R,Theta,Phi,n,l,m):
    Psi = funkfal(R, Theta, Phi, n, l, m)
    FPrawd = np.abs(Psi)**2
    return np.asarray(FPrawd, dtype=float)

def sf_na_kart(R, Theta, Phi):
    X = R*np.sin(Theta)*np.cos(Phi)
    Y = R*np.sin(Theta)*np.sin(Phi)
    Z = R*np.cos(Theta)

    return X, Y, Z

def plot_opengl(n,l,m):
    R, Theta, Phi = przestrz(n)
    Pr = chmuraprawd(R, Theta, Phi, n, l, m)
    cutoff = 0.0001
    mask = Pr > cutoff
    X, Y, Z = sf_na_kart(R[mask], Theta[mask], Phi[mask])
    wart = Pr[mask]
    punkty = np.column_stack((X, Y, Z))
    chmura = pv.PolyData(punkty)
    chmura["prawdopodobienstwo"] = wart

    plotter = pv.Plotter(window_size=[1000, 1000])
    plotter.set_background("black")

    plotter.add_mesh(chmura,
        scalars="prawdopodobienstwo",
        cmap="plasma",
        point_size=5.0,
        render_points_as_spheres=True,
        opacity="linear",
        show_scalar_bar=False)

    plotter.add_text(f"Orbital wodoru: (n={n}, l={l}, m={m})", font_size=12, color="white")
    plotter.show_axes()
    plotter.show()

plot_opengl(n,l,m)