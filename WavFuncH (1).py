import numpy as np
pi = np.pi
from scipy.special import factorial as fact
from scipy.special import genlaguerre as Laguerre
from scipy.special import lpmv as Legendre
import pyvista as pv
from tkinter import *
from tkinter import ttk


n1 = int(input('Wprowadz pierwsza glowna liczbe kwantowa'))
l1 = int(input('Wprowadz pierwsza poboczna liczbe kwantowa'))
m1 = int(input('Wprowadz pierwsza magnetyczna liczbe kwantowa'))

n2 = int(input('Wprowadz druga glowna liczbe kwantowa'))
l2 = int(input('Wprowadz druga poboczna liczbe kwantowa'))
m2 = int(input('Wprowadz druga magnetyczna liczbe kwantowa'))

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

def sf_na_kart(R, Theta, Phi):
    X = R*np.sin(Theta)*np.cos(Phi)
    Y = R*np.sin(Theta)*np.sin(Phi)
    Z = R*np.cos(Theta)

    return X, Y, Z

def main():
    max_n = max(n1, n2)
    R, Theta, Phi = przestrz(max_n)

    FPrzesrz1 = funkfal(R,Theta,Phi,n1,l1,m1)
    Fprzesrz2 = funkfal(R,Theta,Phi,n2,l2,m2)

    PrawdPrzesrz = np.abs(FPrzesrz1) ** 2 + np.abs(Fprzesrz2) ** 2
    cutoff = PrawdPrzesrz.max() * 0.001
    mask = PrawdPrzesrz > cutoff

    FPrzesrz1_mask = FPrzesrz1[mask]
    FPrzesrz2_mask = Fprzesrz2[mask]
    X, Y, Z = sf_na_kart(R[mask], Theta[mask], Phi[mask])
    punkty = np.column_stack((X, Y, Z))

    mu = 1.0
    alpha = np.sqrt(0.00001)
    c = 300000.0

    E1 = -mu*c**2*(-1 + np.sqrt(1 + (2*alpha**2)/(n1 - np.abs(l1+0.5) - 0.5 + np.sqrt((np.abs(l1+0.5)+0.5)**2 - alpha**2))))
    E2 = -mu*c**2*(-1 + np.sqrt(1 + (2*alpha**2)/(n2 - np.abs(l2+0.5) - 0.5 + np.sqrt((np.abs(l2+0.5)+0.5)**2 - alpha**2))))

    chmura = pv.PolyData(punkty)
    chmura["Prawd"] = np.zeros(len(punkty))

    plotter = pv.Plotter(window_size=[1000, 1000])
    plotter.set_background("black")

    plotter.add_mesh(chmura,
                     scalars="Prawd",
                     cmap="plasma",
                     point_size=5.0,
                     render_points_as_spheres=True,
                     opacity="linear",
                     show_scalar_bar=False)

    plotter.show_axes()

    plotter.show(interactive_update=True)

    t = 0.0
    dt = 5.0

    while True:
        try:
            faz1 = np.exp(-1j*E1*t)
            faz2 = np.exp(-1j*E2*t)
            Psi = (FPrzesrz1_mask * faz1) + (FPrzesrz2_mask * faz2)
            Prawd = np.abs(Psi) ** 2

            chmura["Prawd"] = Prawd

            plotter.update()

            if not plotter.render_window.GetGenericDisplayId():
                break

            t += dt
        except AttributeError:
            break

        

if __name__ == "__main__":
    main()