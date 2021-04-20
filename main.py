import pygame as pg
from math import sin, cos, floor, ceil, log
from colorsys import hsv_to_rgb
from numba import njit
import time
from functools import cache
import numpy as np
from PIL import Image, ImageDraw
import tqdm
import os

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIME = (0, 255, 0)
# END COLORS

pg.init()

size = (600, 600)
scale = 1
zoom = 1
position = (0, 0)
RES = 2

display = pg.display.set_mode(size, pg.RESIZABLE)


class Mouse:
    draging = False
    startPos = (0, 0)


def hsvToRgb(h, s, v):
    return tuple(int(i*255) for i in hsv_to_rgb(h/360, s/100, v/100))


def posNegZer(n):
    if n == 0:
        return 0
    elif n < 0:
        return -1
    elif n > 0:
        return 1
    raise ValueError


def isFunction(f):
    def _(): True
    if type(f) in (type(_), type(len)):
        return True
    return False


def pilImageToSurface(pilImage: Image):
    return pg.image.fromstring(
        pilImage.tobytes(), pilImage.size, pilImage.mode).convert()


def tam(x):
    x -= getOfset()[0]
    return (x/(size[0]/RES))*scale


def tamY(y):
    y -= getOfset()[1]
    return (y/(size[1]/RES))*scale


def sem(xr):
    # print(xr)
    # print(xr, size[0]/RES*xr)
    return (xr*(size[0]/RES))/scale + getOfset()[0]


def semY(yr):
    return (yr*(size[1]/RES))/scale + getOfset()[1]


def getOfset():
    return (size[0]/2-position[0], size[1]/2-position[1])


def visibleCoords():
    # return (
    #     (tam(position[0]), tam(size[0]+position[0])),
    #     (tamY(position[1]), tamY(size[1]+position[1]))
    # )
    return (
        (
            -(RES/2-(position[0]/(size[0]/RES))) * scale,
            (RES/2+(position[0]/(size[0]/RES))) * scale
        ),
        (
            -(RES/2-(position[1]/(size[1]/RES))) * scale,
            (RES/2+(position[1]/(size[1]/RES))) * scale
        )
    )


def drawFunc(func, color=WHITE, surface=display):
    for x in range(size[0]):
        xr = tam(x)
        # print(func(xr))
        pg.draw.line(
            surface,
            color(func(xr)) if isFunction(color) else color,
            (x, semY(func(xr))),
            (x+1, semY(func(tam(x+1))))
        )


def drawAreaFunc(func, color=WHITE, surface=display):
    for x in range(size[0]):
        for y in range(size[1]):
            c = color(tam(x), tamY(y)) if isFunction(color) else color
            # print(c)
            # surface.set_at(
            #     func(int(tam(x)), int(tamY(y))),
            #     c
            # )
            pg.draw.line(surface, c, func(x, y), func(x, y))
            # print(surface.get_at(func(x, y)))


def drawAreaFuncImg(func, color=WHITE, surface=display):
    img = Image.new("RGB", size)
    imgDraw = ImageDraw.Draw(img)
    for x in range(size[0]):
        for y in range(size[1]):
            fx, fy = func(x, y)
            # img[fx][fy] = np.array(
            #     color(tam(x), tamY(y))).astype(np.uint8
            # ) if isFunction(color) else color
            imgDraw.point(
                (fx, fy),
                color(tam(x), tamY(y)) if isFunction(color) else color
            )
    # print(dir(img))
    # img = Image.fromarray(img, "RGB")
    # print(dir(img))
    img.save("test.png")
    imgString = img.tobytes()
    surface.blit(pg.image.frombuffer(imgString, size, "RGB"), (0, 0))


def drawMandelBrot(mandelBrotFunc, surface=display):
    img = pilImageToSurface(getMandelBrotImage(mandelBrotFunc))

    surface.blit(img, img.get_rect(center=(250, 250)))


def getMandelBrotImage(mandelBrotFunc):
    img = Image.new("RGB", size, "black")
    imgDraw = ImageDraw.Draw(img)
    # seeX, seeY = visibleCoords()
    # seeX = (floor(seeX[0]), ceil(seeX[1]))
    # seeY = (floor(seeY[0]), ceil(seeY[1]))
    # print(seeX, seeY)
    for x in range(size[0]):
        for y in range(size[1]):
            imgDraw.point(
                (tam(x), tamY(y)),
                fill=hsvToRgb(
                    mandelBrotFunc(tam(x), tamY(y)) * 5 % 360,
                    100,
                    100
                )
            )
    return img


def drawAxis(color=WHITE, surface=display):
    ofset = getOfset()
    pg.draw.line(surface, color, (0, ofset[1]), (size[0], ofset[1]))
    pg.draw.line(surface, color, (ofset[0], 0), (ofset[0], size[1]))
    seeX, seeY = visibleCoords()
    for i in range(floor(seeX[0])*10, ceil(seeX[1])*10):
        pg.draw.line(
            surface,
            color,
            (sem(i/10), ofset[1]-3),
            (sem(i/10), ofset[1]+3)
        )
    for i in range(floor(seeY[0])*10, ceil(seeY[1])*10):
        pg.draw.line(
            surface,
            color,
            (ofset[0]-3, semY(i/10)),
            (ofset[0]+3, semY(i/10))
        )

    for i in range(floor(seeX[0]), ceil(seeX[1])):
        pg.draw.line(
            surface,
            color,
            (sem(i), ofset[1]-10),
            (sem(i), ofset[1]+10)
        )
    for i in range(floor(seeY[0]), ceil(seeY[1])):
        pg.draw.line(
            surface,
            color,
            (ofset[0]-10, semY(i)),
            (ofset[0]+10, semY(i))
        )


def get_iter(c: complex, thresh: int = 4, max_steps: int = 25):
    # Z_(n) = (Z_(n-1))^2 + c
    # Z_(0) = c
    z = c
    i = 1
    while i < max_steps and (z*z.conjugate()).real < thresh:
        z = z*z + c
        i += 1
    return i


def saveMandelbrot(xy, size, zoom, overwrite=False):
    x, y = xy
    if not os.path.exists(
        f"renderedSets/{x}_{y}_{'x'.join(str(i) for i in size)}_{zoom}_set.png"
    ) or overwrite:
        res = 1.1**zoom
        img = Image.new("RGB", size)
        imgDraw = ImageDraw.Draw(img)
        for xr in tqdm.trange(floor(x-size[0]/2), ceil(x+size[0]/2)):
            for yr in tqdm.trange(floor(y-size[1]/2), floor(y+size[1]/2)):
                fx = tam(xr, size=size, scale=res)
                fy = tam(yr, size=size, scale=res)
                # img[fx][fy] = np.array(
                #     color(tam(x), tamY(y))).astype(np.uint8
                # ) if isFunction(color) else color
                # print(xr, yr, xr-x, yr-y, fx, fy)
                imgDraw.point(
                    (xr-x+size[0]/2, yr-y+size[1]/2),
                    hsvToRgb(mandelbrot0(fx, fy)*5 % 360, 100, 100)
                )
        # print(dir(img))
        # img = Image.fromarray(img, "RGB")
        # print(dir(img))
        img.save(
            "renderedSets/"
            f"{x}_{y}_{'x'.join(str(i) for i in size)}_{zoom}_set.png"
        )
        print(res)
        print(
            tam(floor(x-size[0]/2), size=size, scale=res),
            tam(ceil(x+size[0]/2), size=size, scale=res)
        )
        print(
            tam(floor(y-size[1]/2), size=size, scale=res),
            tam(ceil(y+size[1]/2), size=size, scale=res)
        )
        # imgString = img.tobytes()


@cache
@njit
def mandelbrot0(x, y):
    c0 = complex(x, y)
    c = 0
    for i in range(1, 1000):
        if abs(c) > 2:
            return i
        c = c * c + c0
    return 0


@cache
@njit
def mandel(c_r, c_i):
    z_r = 0
    z_i = 0
    z_r_squared = 0
    z_i_squared = 0
    for i in range(1000):
        z_r_squared = z_r * z_r
        z_i_squared = z_i * z_i
        z_r = z_r_squared - z_i_squared + c_r
        z_i = 2 * z_r * z_i + c_i

        if z_r_squared + z_r_squared > 4:
            return i
    return 1000


@cache
@njit
def myFractal(a, b):
    return a+b


@njit
def mandelbrot1(x, y):
    z = complex(x, y)
    c = z
    for n in range(1000):
        if z.real * z.real + z.imag * z.imag > 4.0:
            return n
        z = z*z + c
    return 0


if __name__ == "__main__":
    oldState = None  # (position, RES, scale, zoom, size)

    running = True

    mouse = Mouse()
    while running:
        for u in pg.event.get():
            if u.type == pg.QUIT:
                running = False
            elif u.type == pg.VIDEORESIZE:
                size = (u.w, u.h)
                display = pg.display.set_mode(size, pg.RESIZABLE)
            elif u.type == pg.MOUSEBUTTONDOWN:
                # mouse.startPos = pg.mouse.get_pos()
                pg.mouse.get_rel()
                mouse.draging = True
            elif u.type == pg.MOUSEBUTTONUP:
                mouse.draging = False
            elif u.type == 1027:
                zoom -= posNegZer(u.y)
                if scale < 300:
                    scale = 1.1**zoom
                else:
                    scale -= u.y/10
                if scale == 0:
                    scale = 0.1
                scale = float("%.3g" % scale)
                print(scale, zoom)
                # print(u, dir(u))

        if mouse.draging:
            mouseMov = pg.mouse.get_rel()
            position = tuple(position[i]-mouseMov[i] for i in range(2))
            # print(position, visibleCoords())

        startTime = time.time()

        if oldState != (position, RES, scale, zoom, size):
            display.fill(BLACK)
            # drawAreaFuncImg(
            #     lambda x, y: (x, y),
            #     lambda x, y: hsvToRgb(mandelbrot0(x, y)*5 % 360, 100, 100)
            # )
            drawFunc(
                lambda x: 1.1**x,
                lambda x: hsvToRgb(x*10 % 360, 100, 100)
            )
            drawAxis()

            print(f"Took: {time.time() - startTime}")

        pg.display.update()
        oldState = (position, RES, scale, zoom, size)
        # print(oldState, visibleCoords(), getOfset())
        # print(display.get_buffer().raw)
        # print(pg.image.frombuffer(display.get_buffer(), size, "RGBA"))
        startTime = time.time()
        print(drawMandelBrot(mandel))
        print(f"Took {time.time() - startTime}")
        # quit()
