"""Ещё 12 картин, нарисованных кодом (Kivy graphics). Система координат 1024x1024, y вверх."""
import colorsys
import math
import random

from kivy.graphics import (Color, Ellipse, Line, PopMatrix, PushMatrix,
                           Rectangle, Rotate, Triangle)
from kivy.graphics.texture import Texture

S = 1024


def disc(x, y, r, col):
    Color(*col)
    Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))


def hsv(h, s, v):
    return colorsys.hsv_to_rgb(h % 1.0, s, v)


def grad_tex(colors, h=128):
    buf = bytearray()
    n = len(colors) - 1
    for k in range(h):
        t = (1 - k / (h - 1)) * n
        i = min(int(t), n - 1)
        f = t - i
        a, b = colors[i], colors[i + 1]
        buf += bytes(int(max(0, min(1, a[j] + (b[j] - a[j]) * f)) * 255) for j in range(3))
    tex = Texture.create(size=(1, h), colorfmt="rgb")
    tex.blit_buffer(bytes(buf), colorfmt="rgb", bufferfmt="ubyte")
    tex.mag_filter = tex.min_filter = "linear"
    return tex


def fill(colors, y0=0, h=S):
    Color(1, 1, 1, 1)
    Rectangle(texture=grad_tex(colors), pos=(0, y0), size=(S, h))


def glow(x, y, r, col, a=.12, steps=8):
    for k in range(steps, 0, -1):
        disc(x, y, r * k / steps, (*col, a))


def stars(r, n, ymin=400):
    for _ in range(n):
        disc(r.uniform(0, S), r.uniform(ymin, S), r.uniform(1.2, 3.5), (1, 1, 1, r.uniform(.3, 1)))


def ridges(r, cols, base=380, gap=70, hmin=110, hmax=260, w=190):
    for j, col in enumerate(cols):
        b = base - j * gap
        Color(*col)
        Rectangle(pos=(0, 0), size=(S, b))
        for x in range(-w, S + w, w):
            h = r.uniform(hmin, hmax) - j * 15
            xx = x + r.uniform(-40, 40)
            Triangle(points=[xx, b, xx + w, b + h, xx + 2 * w, b])
    return base - (len(cols) - 1) * gap


def pine(x, y, h, col):
    Color(*col)
    w = h * .42
    Rectangle(pos=(x - w * .07, y - h * .08), size=(w * .14, h * .16))
    for k in range(3):
        sw = w * (1 - k * .25)
        yy = y + k * h * .26
        Triangle(points=[x - sw, yy, x + sw, yy, x, yy + h * (.48 + k * .1)])


def round_tree(x, y, h, trunk, leaf):
    Color(*trunk)
    Rectangle(pos=(x - h * .04, y), size=(h * .08, h * .5))
    disc(x, y + h * .65, h * .3, leaf)
    disc(x - h * .2, y + h * .5, h * .21, leaf)
    disc(x + h * .2, y + h * .5, h * .21, leaf)
    disc(x - h * .06, y + h * .72, h * .16, [min(1, c * 1.25) for c in leaf[:3]] + [.8])


def cloud(x, y, s, col=(1, 1, 1, .92)):
    for k, (dx, dy, rr) in enumerate([(-1, 0, .7), (0, .25, 1), (1, 0, .75), (.3, -.1, .8)]):
        disc(x + dx * s * .8, y + dy * s * .5, s * rr * .6, col)


def autumn():
    r = random.Random(11)
    fill([(.95, .6, .35), (1, .8, .5), (1, .92, .7)])
    glow(760, 560, 170, (1, .95, .7))
    disc(760, 560, 70, (1, .97, .8))
    f = ridges(r, [(.75, .45, .3), (.62, .35, .22), (.5, .28, .18)], base=430, gap=60)
    Color(.3, .18, .1)
    Rectangle(pos=(0, 0), size=(S, f))
    cols = [(.85, .3, .12, 1), (.95, .55, .12, 1), (.98, .78, .2, 1), (.7, .2, .1, 1)]
    for y in sorted((r.uniform(10, f - 10) for _ in range(26)), reverse=True):
        round_tree(r.uniform(-30, S + 30), y, r.uniform(180, 330) * (1.25 - y / f * .5), (.25, .14, .1), r.choice(cols))
    for _ in range(80):
        disc(r.uniform(0, S), r.uniform(0, 600), r.uniform(3, 7), (*r.choice(cols)[:3], .85))


def winter():
    r = random.Random(12)
    fill([(.35, .5, .8), (.75, .8, .95), (1, .88, .88)])
    glow(250, 720, 130, (1, .95, .9))
    disc(250, 720, 55, (1, .98, .95))
    Color(.5, .58, .8)
    Rectangle(pos=(0, 0), size=(S, 440))
    for j, (b, sc) in enumerate([(440, 1.0), (340, .75)]):
        for x in range(-100, S + 100, 270):
            xx, w, h = x + r.uniform(-50, 50), 200 * sc + 40, r.uniform(320, 480) * sc
            Color(.62 - j * .1, .68 - j * .1, .88 - j * .08)
            Triangle(points=[xx - w, b, xx, b + h, xx + w * .15, b])
            Color(.42 - j * .08, .5 - j * .08, .76 - j * .06)
            Triangle(points=[xx, b + h, xx + w, b, xx + w * .15, b])
            Color(1, 1, 1)
            Triangle(points=[xx - w * .3, b + h * .7, xx, b + h, xx + w * .3, b + h * .7])
    Color(.93, .95, 1)
    Rectangle(pos=(0, 0), size=(S, 230))
    for k in range(5):
        Ellipse(pos=(k * 260 - 120, 150 + (k % 2) * 40), size=(420, 170))
    for _ in range(16):
        x, y = r.uniform(0, S), r.uniform(20, 300)
        pine(x, y, 120 + (300 - y) * .6, (.1, .3, .32))
        Color(1, 1, 1, .9)
        Triangle(points=[x - 18, y + 150 * .5, x + 18, y + 150 * .5, x, y + 150 * .75])
    for _ in range(150):
        disc(r.uniform(0, S), r.uniform(0, S), r.uniform(2, 5), (1, 1, 1, .8))


def desert():
    r = random.Random(13)
    fill([(.35, .2, .45), (.9, .4, .3), (1, .75, .4), (1, .9, .6)])
    glow(512, 430, 240, (1, .8, .4))
    disc(512, 430, 110, (1, .93, .65))
    Color(.7, .35, .3)
    Triangle(points=[100, 360, 340, 360, 220, 560])
    Triangle(points=[300, 360, 480, 360, 390, 500])
    for j, (col, b) in enumerate([((.85, .5, .3), 360), ((.8, .4, .25), 270), ((.65, .3, .2), 170), ((.42, .2, .15), 80)]):
        Color(*col)
        Rectangle(pos=(0, 0), size=(S, b))
        for x in range(-200, S + 200, 340):
            Ellipse(pos=(x + r.uniform(-60, 60), b - 90), size=(520, 180 + j * 25))
    Color(.08, .22, .13)
    for cx, cy, h in [(180, 60, 300), (850, 100, 210)]:
        Rectangle(pos=(cx - 16, cy), size=(32, h))
        disc(cx, cy + h, 16, (.08, .22, .13))
        for sgn in (-1, 1):
            Rectangle(pos=(cx + sgn * 42 - 11, cy + h * .45), size=(22, h * .3))
            Rectangle(pos=(min(cx, cx + sgn * 42), cy + h * .45), size=(42, 22))
            disc(cx + sgn * 42, cy + h * .75, 11, (.08, .22, .13))


def sakura():
    r = random.Random(14)
    fill([(.95, .7, .8), (1, .85, .88), (1, .95, .92)])
    glow(790, 760, 130, (1, .97, .9))
    disc(790, 760, 70, (1, .98, .93))
    ridges(r, [(.88, .78, .92), (.78, .68, .88)], base=480, gap=60, hmin=100, hmax=200)
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.85, .8, .92), (.5, .6, .85)]), pos=(0, 0), size=(S, 330))
    Color(.25, .15, .17)
    Line(bezier=(150, 0, 220, 300, 140, 500, 330, 700), width=22)
    Line(bezier=(250, 330, 420, 420, 560, 520, 700, 640), width=12)
    Line(bezier=(200, 420, 120, 560, 160, 680, 80, 820), width=10)
    for _ in range(300):
        a = r.uniform(0, 6.28)
        d = r.uniform(0, 1) ** .6 * 360
        disc(380 + math.cos(a) * d * 1.2, 720 + math.sin(a) * d * .65, r.uniform(14, 34),
             (1, r.uniform(.65, .85), r.uniform(.78, .9), .6))
    for _ in range(110):
        disc(r.uniform(0, S), r.uniform(0, 520), r.uniform(4, 9), (1, .85, .9, .85))


def underwater():
    r = random.Random(15)
    fill([(.05, .6, .75), (.03, .35, .55), (.02, .14, .3)])
    for _ in range(7):
        x = r.uniform(100, 950)
        Color(1, 1, .8, .06)
        Triangle(points=[x - 35, S, x + 35, S, x + r.uniform(-250, 250), 0])
    Color(.85, .75, .55)
    Ellipse(pos=(-250, -200), size=(S + 500, 440))
    for _ in range(16):
        x = r.uniform(0, S)
        col = hsv(r.choice([0, .05, .9, .55, .12]), .65, 1)
        for k in range(3):
            hh = r.uniform(90, 240)
            Color(*col)
            Rectangle(pos=(x + k * 24, 140), size=(13, hh))
            disc(x + k * 24 + 6, 140 + hh, 12, col)
    for _ in range(10):
        x, y, s = r.uniform(80, 900), r.uniform(330, 850), r.uniform(60, 120)
        col = hsv(r.choice([.02, .08, .55, .9]), .8, 1)
        Color(*col)
        Ellipse(pos=(x, y), size=(s, s * .5))
        Triangle(points=[x + 6, y + s * .25, x - s * .3, y + s * .5, x - s * .3, y])
        disc(x + s * .78, y + s * .3, s * .05, (0, 0, 0, 1))
    for _ in range(40):
        Color(1, 1, 1, .5)
        Line(circle=(r.uniform(0, S), r.uniform(200, S), r.uniform(4, 16)), width=1.6)


def aurora():
    r = random.Random(16)
    fill([(.01, .02, .08), (.03, .1, .2), (.05, .2, .3)])
    stars(r, 170, 300)
    for band, col in enumerate([(.2, 1, .6), (.55, .4, 1)]):
        for x in range(0, S, 8):
            y = 540 + band * 80 + 80 * math.sin(x / 130 + band * 2) + 40 * math.sin(x / 47)
            hh = 250 + 110 * math.sin(x / 90 + band)
            for k in range(8):
                Color(*col, .6 * (1 - k / 8))
                Rectangle(pos=(x, y + hh * k / 8), size=(8, hh / 8 + 1))
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.06, .2, .3), (.02, .08, .15)]), pos=(0, 0), size=(S, 260))
    ridges(r, [(.05, .1, .2), (.03, .06, .14)], base=330, gap=60, hmin=70, hmax=150)
    for _ in range(14):
        pine(r.uniform(0, S), r.uniform(10, 200), r.uniform(140, 260), (.01, .03, .06, 1))
    Color(.03, .03, .06)
    Rectangle(pos=(700, 90), size=(130, 80))
    Triangle(points=[690, 170, 840, 170, 765, 240])
    disc(765, 125, 30, (1, .8, .35, .25))
    Color(1, .8, .35)
    Rectangle(pos=(750, 108), size=(30, 34))


def islands():
    r = random.Random(17)
    fill([(.4, .5, .9), (.8, .65, .95), (1, .8, .85), (1, .93, .8)])
    glow(512, 300, 280, (1, .95, .8))
    disc(512, 300, 90, (1, .98, .9))
    for cx, cy in [(150, 880), (820, 900), (560, 560), (230, 480)]:
        cloud(cx, cy, 80)
    for x, y, w in [(150, 300, 110), (720, 500, 170), (560, 820, 100), (300, 640, 230)]:
        Color(.45, .35, .4)
        Triangle(points=[x - w, y, x + w, y, x, y - w * 1.15])
        Color(.33, .26, .33)
        Triangle(points=[x, y, x + w, y, x, y - w * 1.15])
        Color(.4, .75, .4)
        Ellipse(pos=(x - w, y - w * .13), size=(2 * w, w * .32))
        Color(.55, .85, .5)
        Ellipse(pos=(x - w * .9, y - w * .02), size=(1.8 * w, w * .2))
        for _ in range(3):
            round_tree(x + r.uniform(-.6, .6) * w, y + w * .06, w * .55, (.4, .28, .2, 1), (.25, .6, .35, 1))
        if w > 150:
            Color(.75, .92, 1, .85)
            Rectangle(pos=(x + w * .3, y - w * .95), size=(w * .1, w * .85))
    for _ in range(40):
        disc(r.uniform(0, S), r.uniform(0, S), r.uniform(2, 4), (1, 1, 1, .7))


def castle():
    r = random.Random(18)
    fill([(.04, .04, .18), (.2, .12, .4), (.55, .3, .5)])
    stars(r, 120, 450)
    glow(790, 800, 150, (1, .95, .8), .1)
    disc(790, 800, 80, (1, .98, .88))
    ridges(r, [(.14, .1, .28), (.09, .07, .2)], base=330, gap=70)
    Color(.05, .04, .1)
    Triangle(points=[260, 0, 820, 0, 540, 430])
    Rectangle(pos=(0, 0), size=(S, 120))
    for x, w, h, rh in [(380, 70, 250, 130), (630, 70, 320, 130), (505, 80, 210, 150)]:
        Rectangle(pos=(x, 400), size=(w, h + 140))
        Triangle(points=[x - 10, 400 + h + 140, x + w + 10, 400 + h + 140, x + w / 2, 400 + h + 140 + rh])
    Rectangle(pos=(330, 400), size=(380, 170))
    Color(1, .8, .3)
    for x, y in [(405, 600), (655, 650), (535, 620), (480, 480), (570, 480), (400, 470), (650, 470), (535, 700)]:
        Rectangle(pos=(x, y), size=(14, 24))
    Color(0, 0, 0, .8)
    for _ in range(7):
        x, y = r.uniform(80, 520), r.uniform(700, 950)
        Line(points=[x - 16, y + 7, x, y, x + 16, y + 7], width=2)


def alien():
    r = random.Random(19)
    fill([(.08, .02, .25), (.4, .1, .5), (.1, .6, .6)])
    stars(r, 90, 300)
    disc(230, 760, 150, (.9, .6, 1))
    disc(190, 800, 150, (.3, .1, .5, .22))
    PushMatrix()
    Rotate(angle=-20, origin=(230, 760))
    Color(1, .85, 1, .8)
    Line(ellipse=(230 - 260, 760 - 50, 520, 100), width=7)
    PopMatrix()
    disc(700, 880, 48, (.8, 1, 1))
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.1, .38, .4), (.04, .1, .22)]), pos=(0, 0), size=(S, 360))
    for k in range(4):
        Color(.08, .3, .35, 1)
        Ellipse(pos=(k * 300 - 150, 250), size=(500, 160))
    for _ in range(20):
        x, y, h = r.uniform(0, S), r.uniform(20, 300), r.uniform(120, 330)
        col = r.choice([(.3, 1, 1), (1, .4, .85), (.6, .5, 1)])
        glow(x, y, 70, col, .06)
        w = h * .09
        Color(*col, .95)
        Triangle(points=[x - w, y, x, y + h, x + w, y])
        Color(1, 1, 1, .35)
        Triangle(points=[x - w, y, x, y + h, x, y])
    for _ in range(7):
        x, y = r.uniform(60, 960), r.uniform(20, 160)
        Color(.8, .85, .9)
        Rectangle(pos=(x - 7, y), size=(14, 60))
        glow(x, y + 70, 70, (.4, 1, .8), .07)
        disc(x, y + 62, 46, (.35, 1, .8, .9))
    for _ in range(40):
        disc(r.uniform(0, S), r.uniform(150, 700), r.uniform(3, 6), (.6, 1, .9, .8))


def cyber():
    r = random.Random(20)
    fill([(.05, 0, .2), (.4, .05, .45), (1, .3, .5)])
    glow(512, 540, 260, (1, .5, .5), .06)
    disc(512, 540, 190, (1, .8, .4))
    for k in range(6):
        Color(.55, .1, .45)
        Rectangle(pos=(322, 380 + k * 32), size=(380, 5 + k * 3))
    for layer, (col, hmin, hmax) in enumerate([((.16, .03, .3), 200, 520), ((.03, 0, .1), 120, 420)]):
        x = -20
        while x < S:
            w, h = r.uniform(70, 140), r.uniform(hmin, hmax)
            Color(*col)
            Rectangle(pos=(x, 160), size=(w, h))
            if layer == 1:
                for yy in range(int(190), int(160 + h - 20), 28):
                    for xx in range(int(x + 10), int(x + w - 16), 22):
                        if r.random() < .35:
                            Color(*r.choice([(.2, 1, .9), (1, .3, .7), (1, .85, .3)]), .9)
                            Rectangle(pos=(xx, yy), size=(10, 14))
                if r.random() < .4:
                    ny = 160 + h * r.uniform(.4, .8)
                    glow(x + w - 2, ny, 55, (1, .2, .6), .08)
                    Color(1, .3, .7)
                    Rectangle(pos=(x + w - 6, ny - 40), size=(8, 80))
            x += w + 6
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.1, 0, .2), (.02, 0, .06)]), pos=(0, 0), size=(S, 170))
    for _ in range(14):
        x = r.uniform(0, S)
        Color(*r.choice([(.2, 1, .9), (1, .3, .7)]), .35)
        Rectangle(pos=(x, 0), size=(5, 160))


def fairy():
    r = random.Random(21)
    fill([(.02, .1, .12), (.05, .25, .2), (.15, .4, .25)])
    for x in (200, 450, 700, 900):
        Color(1, 1, .7, .07)
        Triangle(points=[x - 30, S, x + 30, S, x + r.uniform(-250, 150), 0])
    for _ in range(9):
        x, w = r.uniform(0, S), r.uniform(50, 100)
        Color(.04 + r.random() * .03, .09, .07)
        Rectangle(pos=(x, 0), size=(w, S))
    for _ in range(5):
        disc(r.uniform(0, S), r.uniform(150, 450), r.uniform(120, 200), (.7, 1, .9, .05))
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.07, .28, .16), (.02, .1, .08)]), pos=(0, 0), size=(S, 230))
    for _ in range(11):
        x, y, s = r.uniform(30, 990), r.uniform(10, 200), r.uniform(40, 100)
        col = hsv(r.choice([.85, .55, .1]), .6, 1)
        glow(x, y + s * .5, s * 1.3, col, .05)
        Color(.9, .88, .8)
        Rectangle(pos=(x - s * .1, y), size=(s * .2, s * .6))
        Color(*col)
        Ellipse(pos=(x - s * .5, y + s * .45), size=(s, s * .6))
    for _ in range(70):
        x, y = r.uniform(0, S), r.uniform(60, 900)
        glow(x, y, 20, (1, .95, .4), .12, 4)
        disc(x, y, 3, (1, 1, .8, 1))


def lighthouse():
    r = random.Random(22)
    fill([(.03, .05, .12), (.12, .18, .3), (.4, .45, .55)])
    glow(790, 810, 140, (.9, .95, 1), .1)
    disc(790, 810, 70, (.97, .98, 1))
    for _ in range(9):
        disc(r.uniform(0, S), r.uniform(560, 760), r.uniform(60, 130), (.08, .11, .2, .85))
    Color(1, 1, .8, .17)
    Triangle(points=[330, 745, 1100, 940, 1100, 560])
    Color(1, 1, 1)
    Rectangle(texture=grad_tex([(.1, .22, .38), (.02, .06, .15)]), pos=(0, 0), size=(S, 380))
    for row in range(9):
        for x in range(-60 + (row % 2) * 50, S + 60, 100):
            Color(1, 1, 1, .08 + row * .008)
            Ellipse(pos=(x, 20 + row * 40), size=(80, 10))
    Color(.07, .07, .1)
    Ellipse(pos=(150, 240), size=(400, 220))
    Triangle(points=[200, 300, 500, 300, 360, 470])
    Color(.93, .91, .88)
    Triangle(points=[285, 400, 375, 400, 302, 720])
    Triangle(points=[375, 400, 358, 720, 302, 720])
    Color(.75, .15, .15)
    Rectangle(pos=(296, 470), size=(68, 50))
    Rectangle(pos=(300, 590), size=(60, 50))
    Color(1, .92, .5)
    Rectangle(pos=(300, 720), size=(60, 50))
    glow(330, 745, 100, (1, .95, .6), .08)
    Color(.1, .1, .14)
    Triangle(points=[292, 770, 368, 770, 330, 830])
    for _ in range(90):
        x, y = r.uniform(0, S), r.uniform(0, S)
        Color(.8, .88, 1, .22)
        Line(points=[x, y, x - 14, y - 42], width=1.4)


SCENES2 = [
    ("autumn", "Золотая осень", "Природа", autumn),
    ("winter", "Зимние горы", "Природа", winter),
    ("desert", "Пустыня на закате", "Природа", desert),
    ("sakura", "Сакура у реки", "Природа", sakura),
    ("underwater", "Подводный мир", "Природа", underwater),
    ("aurora", "Северное сияние", "Природа", aurora),
    ("lighthouse", "Маяк в шторм", "Природа", lighthouse),
    ("islands", "Плавучие острова", "Фантастика", islands),
    ("castle", "Замок под луной", "Фантастика", castle),
    ("alien", "Чужая планета", "Фантастика", alien),
    ("cyber", "Неоновый город", "Фантастика", cyber),
    ("fairy", "Волшебный лес", "Фантастика", fairy),
]
