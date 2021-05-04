from multiprocessing import Pool
from numba import njit


def getMandelBrotImageMP(size):
    coords = []
    for x in range(size[0]):
        for y in range(size[1]):
            # coords[(x+1)*y] = (x,y)
            coords.append((x, y))
    with Pool() as pool:
        brot = pool.starmap(mandelbrot1, coords)
    print(brot)
    return brot


@njit
def mandelbrot1(x, y):
    z = complex(x, y)
    c = z
    for n in range(1000):
        if z.real * z.real + z.imag * z.imag > 4.0:
            return n
        z = z*z + c
    return 0
