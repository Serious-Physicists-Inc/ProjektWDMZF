import numpy as np
import matplotlib.pyplot as plt
pi = np.pi
from scipy.special import factorial as fact
from scipy.special import genlaguerre as Laguerre
from scipy.special import lpmv as Legendre

n = int(input('Wprowadz glowna liczbe kwantowa'))
l = int(input('Wprowadz poboczna liczbe kwantowa'))
m = int(input('Wprowadz magnetyczna liczbe kwantowa'))

def przestrz(n,Z=1):
    rmax =  10*n**2/Z 
    r = np.linspace(0, rmax, 50)
    theta = np.linspace(0, np.pi, 50)
    phi = np.linspace(0, 2*np.pi, 50)

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

    rad = np.sqrt((2/(n*a0))**3*fact(n-l-1)/(2*n*fact(l+1)**3))*(2/(n*a0))**l*L*np.exp(-R/(n*a0))

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

def cutoff_wartosc(Pr, proc = 0.93):
    R, Theta, Phi = przestrz(n)
    Pr = chmuraprawd(R, Theta, Phi, n, l, m)
    Prf = Pr.reshape(-1)
    Prs = np.sort(Prf)
    tot_praw = Prs.sum()
    sum_doc = tot_praw * proc
    mal_sort = Prs[::-1]
    kumulac_sum = np.cumsum(mal_sort)
    cutoffi = np.argmax(kumulac_sum >= sum_doc)
    Vcutoff = mal_sort[cutoffi]
    return Vcutoff

def plot_chmur(R, Theta, Phi,proc = 0.93):
    R, Theta, Phi = przestrz(n)
    X, Y, Z = sf_na_kart(R, Theta, Phi)
    Pr = chmuraprawd(R, Theta, Phi, n, l ,m)
    Pr = Pr / Pr.max()
    cutoff = cutoff_wartosc(Pr, proc)
    mask = Pr > cutoff

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(X[mask], Y[mask], Z[mask], c=Pr[mask], cmap='plasma', s=1, alpha=0.5)
    plt.show()

plot_chmur(n,l,m,)