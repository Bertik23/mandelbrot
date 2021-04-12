import pygame as pg
from math import sin, cos

pg.init()

size = (600, 600)
scale = 1
position = (0,0)
RES = 10

display = pg.display.set_mode(size, pg.RESIZABLE)

class Mouse:
    draging = False
    startPos = (0, 0)

def tam(x):
    if x == 0:
        return 0
    return x/(size[0]/RES)

def sem(xr):
    # print(xr, size[0]/RES*xr)
    if xr == 0:
        return 0
    return xr*(size[0]/RES)

def semY(yr):
    return yr*(size[1]/RES)

def getOfset():
    return (size[0]/2-position[0], size[1]/2-position[1])

def drawFunc(func, surface=display):
    ofset = getOfset()
    for x in range(size[0]):
        xr = tam(x-ofset[0])
        # print(func(tam(x+1-ofset[0])))
        pg.draw.line(surface, (255, 255, 255), (x, semY(func(xr))+ofset[1]), (x+1, semY(func(tam(x+1-ofset[0])))+ofset[1]))
        # print(x, func(x), xr, func(xr), tam(x+1), func(tam(x+1)), (x, sem(func(xr))+ofset[1]), (x+1, sem(func(tam(x+1-ofset[1])))+ofset[1]))
        
def drawAxis(surface=display):
    ofset = getOfset()
    pg.draw.line(surface, (255, 255, 255), (0, ofset[1]), (size[0], ofset[1]))
    pg.draw.line(surface, (255, 255, 255), (ofset[0], 0), (ofset[0], size[1]))
    for i in range(RES*10):
        pg.draw.line(surface, (255, 255, 255), (sem(i/10)-position[0], ofset[1]-3), (sem(i/10)-position[0], ofset[1]+3))
        pg.draw.line(surface, (255, 255, 255), (ofset[0]-3, semY(i/10)-position[1]), (ofset[0]+3, semY(i/10)-position[1]))
        
    for i in range(RES):
        pg.draw.line(surface, (255, 255, 255), (sem(i)-position[0], ofset[1]-10), (sem(i)-position[0], ofset[1]+10))
        pg.draw.line(surface, (255, 255, 255), (ofset[0]-10, semY(i)-position[1]), (ofset[0]+10, semY(i)-position[1]))
        
running = True

mouse = Mouse()
while running:
    display.fill((0, 0, 0))
    for u in pg.event.get():
        if u.type == pg.QUIT:
            running = False
        if u.type == pg.VIDEORESIZE:
            size = (u.w, u.h)
            display = pg.display.set_mode(size, pg.RESIZABLE)
        if u.type == pg.MOUSEBUTTONDOWN:
            # mouse.startPos = pg.mouse.get_pos()
            pg.mouse.get_rel()
            mouse.draging = True
        if u.type == pg.MOUSEBUTTONUP:
            mouse.draging = False
            
    if mouse.draging:
        mouseMov = pg.mouse.get_rel()
        position = tuple(position[i]-mouseMov[i] for i in range(2))
            
    drawFunc(lambda x: sin(x))
    drawAxis()
    
    pg.display.update()
    # quit()
    

