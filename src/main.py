from model import Atom, State
from plot import Plot

def main():
    plot = Plot()

    states = (State(2, 1, 0), State(3,2,1))
    atom = Atom(*states)
    plot.draw(atom.cart_grid())
    plot.show()

if __name__ == "__main__":
    main()

input("Naciśnij Enter, aby zakończyć...")