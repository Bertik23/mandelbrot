import pygame as pg
from math import sin, cos, floor, ceil, log
from colorsys import hsv_to_rgb
from numba import njit
import time
from functools import cache
import numpy as np
from PIL import Image, ImageDraw
import os
from threading import Thread
from pprint import pprint
from queue import LifoQueue, Empty

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIME = (0, 255, 0)
# END COLORS


FPS = 30
size = (600, 600)
scale = 1
zoom = 1
position = (0, 0)
RES = 2
mandelBrotCache = {}
mandelBrotQueue = LifoQueue()
imageQueue = LifoQueue()
positionSnap = 1
running = True
lastImageBuffer = (Image.new("RGB", size), (0, 0))
# imageTimes = [time.time()]

pg.init()
display = pg.display.set_mode(size, pg.RESIZABLE | pg.HWSURFACE | pg.DOUBLEBUF)

if not os.path.exists("renderedSets"):
    os.mkdir("renderedSets")


class Mouse:
    draging = False
    startPos = (0, 0)
    lastDragFrame = 0


class ImageBuffer:
    def __init__(self):
        self.images: dict[int, Image.Image] = {}
        self.positions: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}

    def __getitem__(self, i: int):
        return self.images[i], self.positions[i]

    def __setitem__(
        self,
        key: int,
        value: tuple[Image.Image, tuple[tuple[int, int], tuple[int, int]]]
    ):
        self.images[key] = value[0]
        self.positions[key] = value[1]

    def addToZoom(self, zoom: int, image: Image.Image, pos: tuple(int, int)):
        newSize = image.size


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


def roundToNearest(n, base):
    return base*round(n/base)


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
    return (xr*(size[0]/RES))/scale + getOfset()[0]


def semY(yr):
    return (yr*(size[1]/RES))/scale + getOfset()[1]


def getOfset():
    return (
        size[0]/2-position[0],
        size[1]/2-position[1]
    )


def visibleCoords():
    return (
        (tam(0), tam(size[0])),
        (tamY(0), tamY(size[1]))
    )


def tamC(x, pos, scale):
    x -= getOfsetC(pos)[0]
    return (x/(size[0]/RES))*scale


def tamYC(y, pos, scale):
    y -= getOfsetC(pos)[1]
    return (y/(size[1]/RES))*scale


def semC(xr, pos, scale):
    return (xr*(size[0]/RES))/scale + getOfsetC(pos)[0]


def semYC(yr, pos, scale):
    return (yr*(size[1]/RES))/scale + getOfsetC(pos)[1]


def getOfsetC(pos):
    return (size[0]/2-pos[0], size[1]/2-pos[1])


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
            pg.draw.line(surface, c, func(x, y), func(x, y))


def drawAreaFuncImg(func, color=WHITE, surface=display):
    img = Image.new("RGB", size)
    imgDraw = ImageDraw.Draw(img)
    for x in range(size[0]):
        for y in range(size[1]):
            fx, fy = func(x, y)
            imgDraw.point(
                (fx, fy),
                color(tam(x), tamY(y)) if isFunction(color) else color
            )

    surface.blit(pilImageToSurface(img), (0, 0))


def getMandelBrotImage(mandelBrotFunc, pos, scale):
    if os.path.exists(
        "renderedSets/"
        f"{tamC(0, pos, scale), tamYC(0, pos, scale)}__"
        f"{tamC(size[0], pos, scale), tamYC(size[1], pos, scale)}.png"
    ):
        img = Image.open(
            "renderedSets/"
            f"{tamC(0, pos, scale), tamYC(0, pos, scale)}__"
            f"{tamC(size[0], pos, scale), tamYC(size[1], pos, scale)}.png"
        )
    else:
        img = Image.new("RGB", size, "black")
        imgDraw = ImageDraw.Draw(img)
        for x in range(size[0]):
            for y in range(size[1]):
                color = hsvToRgb(
                    mandelBrotFunc(
                        tamC(x, pos, scale), tamYC(y, pos, scale)
                    ) * 5 % 360,
                    100,
                    100
                )
                imgDraw.point(
                    (x, y),
                    color
                )
        img.save(
            "renderedSets/"
            f"{tamC(0, pos, scale), tamYC(0, pos, scale)}__"
            f"{tamC(size[0], pos, scale), tamYC(size[1], pos, scale)}.png"
        )
    return img


def drawImage(image, coords=(0, 0), surface=display):
    surface.blit(pilImageToSurface(image), coords)


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


@cache
@njit
def mandelParts(c_r, c_i):
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


def calculateMandel(mandelBrotFunc):
    global lastImageBuffer
    while running:
        pos, scale = mandelBrotQueue.get()
        imageQueue.put((
            getMandelBrotImage(mandelBrotFunc, pos, scale),
            (tamC(0, pos, scale), tamYC(0, pos, scale))
        ))
        mandelBrotQueue.task_done()


@cache
@njit
def mandelComplex(x, y):
    z = complex(x, y)
    c = z
    for n in range(1000):
        if z.real * z.real + z.imag * z.imag > 4.0:
            return n
        z = z*z + c
    return 0


timeDelta = 0
frame = 0


def main():
    global position, scale, RES, zoom, size, display, running, timeDelta
    global frame, lastImageBuffer
    calcThread = Thread(
        target=calculateMandel,
        args=(mandelComplex,),
        name="BrotCalculation"
    )
    calcThread.start()

    oldState = None

    mouse = Mouse()
    while running:
        for u in pg.event.get():
            if u.type == pg.QUIT:
                running = False
            elif u.type == pg.VIDEORESIZE:
                size = (u.w, u.h)
                display = pg.display.set_mode(size, pg.RESIZABLE)
            elif u.type == pg.MOUSEBUTTONDOWN:
                pg.mouse.get_rel()
                mouse.draging = True
            elif u.type == pg.MOUSEBUTTONUP:
                mouse.draging = False
                mouse.lastDragFrame = frame
            elif u.type == 1027:
                oldPos = (
                    tam(position[0] + getOfset()[0]),
                    tamY(position[1] + getOfset()[1])
                )
                zoom -= posNegZer(u.y)
                if scale < 300:
                    scale = 1.1**zoom
                else:
                    scale -= u.y/10
                if scale == 0:
                    scale = 0.1
                scale = float("%.3g" % scale)
                position = (
                    sem(oldPos[0]) - getOfset()[0],
                    semY(oldPos[1]) - getOfset()[1]
                )

        if mouse.draging:
            mouseMov = pg.mouse.get_rel()
            position = (
                position[0] - roundToNearest(
                    mouseMov[0],
                    positionSnap
                ),
                position[1] - roundToNearest(
                    mouseMov[1],
                    positionSnap
                )
            )

        startTime = time.time()

        try:
            lastImageBuffer = imageQueue.get_nowait()
            rerender = True
        except Empty:
            rerender = False

        if (
            oldState != (position, RES, scale, zoom, size)
            or mouse.lastDragFrame >= frame-2 or rerender
        ):
            display.fill(BLACK)
            if not mouse.draging or mouse.lastDragFrame >= frame-2:
                if mandelBrotQueue.empty():
                    # mandelBrotQueue.put((position, scale))
                    pass
                pass

            drawImage(
                lastImageBuffer[0],
                (sem(lastImageBuffer[1][0]), semY(lastImageBuffer[1][1]))
            )
            drawFunc(
                lambda x: 1.1**x,
                lambda x: hsvToRgb(x*10 % 360, 100, 100)
            )
            drawAxis()

            # print(f"Took: {time.time() - startTime}")

        pg.display.update()
        oldState = (position, RES, scale, zoom, size)
        # print(oldState, visibleCoords(), getOfset())
        # print(display.get_buffer().raw)
        # print(pg.image.frombuffer(display.get_buffer(), size, "RGBA"))
        startTime = time.time()
        # print(getMandelBrotImageMP(size))
        timeDelta = time.time() - startTime
        # print(f"Took {timeDelta}")

        frame += 1

    calcThread.join()


if __name__ == "__main__":
    main()
    pass
