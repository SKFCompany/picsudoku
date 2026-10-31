import colorsys
import json
import os
import random

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import (ClearBuffers, ClearColor, Color, Ellipse, Fbo, Line,
                           PopMatrix, PushMatrix, Rectangle, RoundedRectangle,
                           Rotate, Scale, Triangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget
from kivymd.app import MDApp

from scenes2 import SCENES2

# ───────────────────────── палитра ─────────────────────────
BG = (0.05, 0.06, 0.12, 1)
PANEL = (0.11, 0.13, 0.22, 1)
PANEL2 = (0.16, 0.19, 0.31, 1)
TXT = (0.93, 0.95, 1, 1)
MUTED = (0.6, 0.66, 0.82, 1)
ACC = (0.35, 0.85, 0.9, 1)
GOLD = (1, 0.8, 0.35, 1)
RED = (1, 0.38, 0.42, 1)
HL = (0.2, 0.25, 0.42, 1)
SAME = (0.28, 0.38, 0.6, 1)
SELC = (0.2, 0.55, 0.65, 1)

DIFFS = [("Лёгкий", 10, 4, 3), ("Средний", 15, 6, 3), ("Сложный", 20, 8, 3), ("Мастер", 25, 10, 4)]
# название, клеток в стороне сектора, цветов (с фоном), секторов по стороне картины

# ───────────────────────── рисование картинок ─────────────────────────
S = 1024


def disc(x, y, r, col):
    Color(*col)
    Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))


def hsv(h, s, v):
    return colorsys.hsv_to_rgb(h % 1.0, s, v)


def grad_tex(colors, h=128):
    """Вертикальный градиент: colors[0] — верх, colors[-1] — низ."""
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
    tex.mag_filter = "linear"
    tex.min_filter = "linear"
    return tex


def sky(colors, y0=0, h=S):
    Color(1, 1, 1, 1)
    Rectangle(texture=grad_tex(colors), pos=(0, y0), size=(S, h))


def pine(x, y, h, col):
    Color(*col)
    w = h * 0.42
    Rectangle(pos=(x - w * 0.07, y - h * 0.08), size=(w * 0.14, h * 0.16))
    for k in range(3):
        sw = w * (1 - k * 0.25)
        yy = y + k * h * 0.26
        Triangle(points=[x - sw, yy, x + sw, yy, x, yy + h * (0.48 + k * 0.1)])


def landscape(r, sk, sun_col, sun_pos, sun_r, ridges, water=None, stars=0, deco=None):
    sky(sk)
    for _ in range(stars):
        disc(r.uniform(0, S), r.uniform(S * 0.45, S), r.uniform(1.5, 4), (1, 1, 1, r.uniform(0.4, 1)))
    sx, sy = sun_pos
    for k in range(7, 0, -1):
        disc(sx, sy, sun_r + k * 38, (*sun_col, 0.06))
    disc(sx, sy, sun_r, (*sun_col, 1))
    base = 380
    for j, col in enumerate(ridges):
        b = base - j * 70
        Color(*col)
        Rectangle(pos=(0, 0), size=(S, b))
        for x in range(-150, S + 150, 190):
            h = r.uniform(110, 260) - j * 22
            xx = x + r.uniform(-40, 40)
            Triangle(points=[xx, b, xx + 190, b + h, xx + 380, b])
    front = base - (len(ridges) - 1) * 70
    if water:
        Color(1, 1, 1, 1)
        Rectangle(texture=grad_tex(water), pos=(0, 0), size=(S, front))
        Color(*sun_col, 0.4)
        for k in range(9):
            w = 220 - k * 20
            Rectangle(pos=(sx - w / 2, front - 20 - k * 16), size=(w, 7))
    if deco == "pines":
        for _ in range(16):
            pine(r.uniform(0, S), r.uniform(10, front - 10), r.uniform(120, 240), (0.02, 0.05, 0.1, 1))
    if deco == "mist":
        for _ in range(9):
            disc(r.uniform(0, S), r.uniform(front - 20, front + 160), r.uniform(80, 150), (1, 1, 1, 0.1))
        for _ in range(60):
            x, y = r.uniform(0, S), r.uniform(10, front - 10)
            disc(x, y, r.uniform(5, 10), hsv(r.choice([0.0, 0.12, 0.8]), 0.5, 1))


def sc_sunset():
    landscape(random.Random(1), [(.13, .1, .35), (.5, .22, .5), (.97, .45, .4), (1, .78, .45)],
              (1, .85, .5), (512, 470), 120,
              [(.55, .3, .55), (.4, .2, .5), (.28, .15, .4), (.16, .1, .3)],
              water=[(.4, .22, .48), (.12, .08, .25)])


def sc_moon():
    landscape(random.Random(2), [(.02, .03, .12), (.07, .12, .3), (.2, .3, .5)],
              (.95, .95, .85), (700, 720), 80,
              [(.1, .18, .35), (.07, .13, .28), (.04, .09, .2), (.02, .05, .12)],
              stars=140, deco="pines")


def sc_dawn():
    landscape(random.Random(3), [(.55, .75, .9), (.98, .8, .8), (1, .9, .7)],
              (1, .95, .7), (300, 430), 90,
              [(.55, .75, .7), (.4, .65, .55), (.25, .5, .4), (.15, .38, .3)],
              deco="mist")


def sc_space():
    r = random.Random(4)
    sky([(.02, .02, .1), (.12, .04, .28), (.2, .06, .3)])
    for _ in range(7):
        disc(r.uniform(0, S), r.uniform(0, S), r.uniform(120, 260), (*hsv(r.choice([.75, .6, .9]), .8, .8), .07))
    for _ in range(240):
        disc(r.uniform(0, S), r.uniform(0, S), r.uniform(1, 3.5), (1, 1, 1, r.uniform(.3, 1)))
    px, py, pr = 660, 420, 230
    disc(px, py, pr, (.95, .55, .3))
    for k in range(6):
        disc(px - 40 + k * 10, py + 20 - k * 8, pr - k * 28, (.7, .25, .2, .13))
    for k in range(4):
        Color(.55, .2, .15, .22)
        Rectangle(pos=(px - pr + 20 + k * 6, py - 120 + k * 70), size=(2 * pr - 40 - k * 12, 22))
    disc(px - 80, py + 90, 60, (1, .85, .6, .12))
    PushMatrix()
    Rotate(angle=-18, origin=(px, py))
    for k, a in enumerate((.9, .6, .4)):
        Color(1, .88, .6, a)
        Line(ellipse=(px - 330 - k * 22, py - 70 - k * 8, 660 + k * 44, 140 + k * 16), width=dp(5) - k)
    PopMatrix()
    disc(190, 760, 70, (.6, .8, 1))
    disc(170, 780, 70, (.05, .06, .2, .35))
    disc(280, 190, 34, (.8, .8, .9))


def sc_ocean():
    r = random.Random(5)
    sky([(.3, .6, .95), (.7, .85, 1), (1, .9, .75)])
    for k in range(6, 0, -1):
        disc(720, 640, 100 + k * 34, (1, .95, .7, .08))
    disc(720, 640, 100, (1, .96, .75))
    for cx, cy in [(220, 840), (620, 920), (900, 800)]:
        for k in range(5):
            disc(cx + k * 50 - 100, cy + r.uniform(-15, 15), r.uniform(45, 75), (1, 1, 1, .92))
    hz = 470
    Color(1, 1, 1, 1)
    Rectangle(texture=grad_tex([(.2, .62, .85), (.05, .32, .62), (.02, .15, .4)]), pos=(0, 0), size=(S, hz))
    for row in range(10):
        y = 30 + row * 44
        for x in range(-60 + (row % 2) * 45, S + 60, 90):
            Color(1, 1, 1, .08 + row * .012)
            Ellipse(pos=(x, y), size=(70 - row * 3, 10 + row))
    Color(1, .95, .7, .35)
    for k in range(8):
        w = 200 - k * 20
        Rectangle(pos=(720 - w / 2, hz - 20 - k * 18), size=(w, 6))
    Color(.4, .22, .16, 1)
    Rectangle(pos=(260, 392), size=(150, 38))
    Triangle(points=[410, 430, 410, 392, 450, 430])
    Triangle(points=[260, 430, 260, 392, 232, 430])
    Rectangle(pos=(330, 430), size=(9, 230))
    Color(1, 1, 1, 1)
    Triangle(points=[342, 445, 342, 650, 450, 445])
    Color(1, .93, .8, 1)
    Triangle(points=[326, 445, 326, 600, 235, 445])


def sc_mandala(k):
    def draw():
        r = random.Random(100 + k)
        h = k / 12
        cols = [hsv(h, .55, 1), hsv(h + .12, .5, 1), hsv(h + .5, .4, 1), hsv(h + .62, .5, .95)]
        sky([hsv(h, .6, .3), hsv(h + .08, .7, .12)])
        cx = cy = S / 2
        n = r.choice([6, 8, 10, 12])
        for L in range(5):
            rad = 470 - L * 85
            col = cols[L % 4]
            m = n * (1 + L % 2)
            for i in range(m):
                PushMatrix()
                Rotate(angle=360 / m * i + L * 9, origin=(cx, cy))
                w = rad * 6.28 / m * 0.9
                Color(col[0], col[1], col[2], .9 - L * .08)
                Ellipse(pos=(cx - w / 2, cy + rad * .25), size=(w, rad * .75))
                Color(1, 1, 1, .25)
                Ellipse(pos=(cx - w * .18, cy + rad * .45), size=(w * .36, rad * .35))
                PopMatrix()
        disc(cx, cy, 60, (1, 1, 1, .95))
        disc(cx, cy, 34, cols[0])
    return draw


BASE = os.path.dirname(os.path.abspath(__file__))
_BASE_PICS = [("sunset", "Закат у озера", "Природа", sc_sunset),
              ("moon", "Лунная ночь", "Природа", sc_moon),
              ("dawn", "Рассвет в долине", "Природа", sc_dawn),
              ("ocean", "Морской бриз", "Природа", sc_ocean),
              ("space", "Космос", "Фантастика", sc_space)]


def scan_packs():
    """assets/pics/<Категория>/*.jpg|png и assets/stickers/*.jpg|png (+ assets/credits.json)."""
    base = os.path.join(BASE, "assets")
    try:
        with open(os.path.join(base, "credits.json"), encoding="utf-8") as f:
            credits = json.load(f)
    except Exception:
        credits = {}
    ext = (".jpg", ".jpeg", ".png")
    pics, stick = [], []
    pd = os.path.join(base, "pics")
    if os.path.isdir(pd):
        for cat in sorted(os.listdir(pd)):
            cd = os.path.join(pd, cat)
            if not os.path.isdir(cd):
                continue
            for fn in sorted(os.listdir(cd)):
                if fn.lower().endswith(ext):
                    rel = cat + "/" + fn
                    c = credits.get(rel, {})
                    title = c.get("title") or os.path.splitext(fn)[0].replace("_", " ").replace("-", " ")
                    pics.append(dict(id="f:" + rel, title=title[:60], cat=cat,
                                     src=os.path.join(cd, fn), author=c.get("author", "")))
    sd = os.path.join(base, "stickers")
    if os.path.isdir(sd):
        for fn in sorted(os.listdir(sd)):
            if fn.lower().endswith(ext):
                stick.append(dict(id="f:" + fn, src=os.path.join(sd, fn)))
    return pics, stick


PICS = [dict(id=i, title=t, cat=c, src=f, author="") for i, t, c, f in _BASE_PICS + SCENES2]
_fp, _fs = scan_packs()
PICS += _fp
PICS += [dict(id="m%d" % k, title="Мандала %d" % (k + 1), cat="Мандалы", src=sc_mandala(k), author="")
         for k in range(24)]
PICS += [dict(id=s["id"], title=os.path.splitext(os.path.basename(s["src"]))[0], cat="Стикеры",
              src=s["src"], author="") for s in _fs]
STICKERS = []
PIC_BY_ID = {p["id"]: p for p in PICS}
ST_BY_ID = {s["id"]: s for s in STICKERS}
CATS = ["Все"] + list(dict.fromkeys(p["cat"] for p in PICS))

_TEX, _FBO, _REG = {}, {}, {}
_CAP = {"p": 12, "s": 60}


def _file_tex(path, size):
    """Картинка из assets (квадратная, fetch_art.py делает 1024x1024). Pillow не нужен: грузит SDL2_image."""
    tex = CoreImage(path).texture
    tex.mag_filter = tex.min_filter = "linear"
    return tex


def get_tex(key):
    t = _TEX.pop(key, None)
    if t is not None:
        _TEX[key] = t
        return t
    item = (PIC_BY_ID if key[0] == "p" else ST_BY_ID)[key[1]]
    size = 1024 if key[0] == "p" else 512
    if callable(item["src"]):
        scale = size / 1024.0
        fbo = Fbo(size=(size, size))
        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            PushMatrix()
            Scale(scale, scale, 1)
            item["src"]()
            PopMatrix()
        fbo.draw()
        _FBO[key] = fbo
        tex = fbo.texture
    else:
        try:
            tex = _file_tex(item["src"], size)
        except Exception:
            tex = grad_tex([(.2, .2, .3), (.1, .1, .2)])
    _TEX[key] = tex
    keys = [k for k in _TEX if k[0] == key[0]]
    while len(keys) > _CAP[key[0]]:
        old = keys.pop(0)
        _TEX.pop(old, None)
        _FBO.pop(old, None)
        for rk in [k for k in _REG if k[0] == old]:
            _REG.pop(rk, None)
    return tex


def get_region(key, n, i):
    k = (key, n, i)
    if k not in _REG:
        tex = get_tex(key)
        r, c = divmod(i, n)
        w, h = tex.width / n, tex.height / n
        _REG[k] = tex.get_region(c * w, (n - 1 - r) * h, w, h)
    return _REG[k]


# ───────────────────────── виджеты ─────────────────────────
class RBtn(ButtonBehavior, Label):
    def __init__(self, text="", bg=PANEL2, fg=TXT, radius=14, **kw):
        kw.setdefault("font_size", sp(15))
        super().__init__(text=text, color=fg, **kw)
        self._bg = bg
        self._rad = radius
        with self.canvas.before:
            self._c = Color(*bg)
            self._r = RoundedRectangle(radius=[dp(radius)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self._r.pos, self._r.size = self.pos, self.size

    def set_bg(self, c):
        self._bg = c
        self._c.rgba = c

    def on_press(self):
        self._c.rgba = [min(1, v + .12) for v in self._bg[:3]] + [1]

    def on_release(self):
        self._c.rgba = self._bg


def lab(text, fs, col=TXT, bold=False, h=None, align="center"):
    l = Label(text=text, font_size=sp(fs), color=col, bold=bold, halign=align, valign="middle")
    l.bind(size=lambda w, s: setattr(w, "text_size", s))
    if h:
        l.size_hint_y = None
        l.height = dp(h)
    return l


class PictureView(Widget):
    fresh = NumericProperty(-1)
    fresh_a = NumericProperty(1)

    def __init__(self, key, grid, unlocked, on_pick=None, **kw):
        super().__init__(**kw)
        self.key, self.grid, self.unlocked = key, grid, set(unlocked)
        self.on_pick = on_pick
        self.lock, self.pick_all, self.ghost = True, False, .2
        self._t0 = None
        self.bind(pos=self.draw, size=self.draw, fresh_a=self.draw)

    def draw(self, *a):
        self.canvas.clear()
        if self.width < 2:
            return
        tex = get_tex(self.key)
        n = self.grid
        x, y, w, h = self.x, self.y, self.width, self.height
        ps = w / n
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=(x, y), size=(w, h))
            Color(1, 1, 1, self.ghost)
            Rectangle(texture=tex, pos=(x, y), size=(w, h))
            for i in range(n * n):
                r, c = divmod(i, n)
                p = (x + c * ps, y + h - (r + 1) * ps)
                if i in self.unlocked:
                    Color(1, 1, 1, self.fresh_a if i == self.fresh else 1)
                    Rectangle(texture=get_region(self.key, n, i), pos=p, size=(ps, ps))
                elif self.lock:
                    Color(.03, .04, .09, .45)
                    Rectangle(pos=p, size=(ps, ps))
                    Color(1, 1, 1, .35)
                    cx, cy = p[0] + ps / 2, p[1] + ps / 2
                    s = min(ps * .14, dp(9))
                    Line(circle=(cx, cy + s * .6, s * .7, 0, 360), width=1.2)
                    Rectangle(pos=(cx - s, cy - s * 1.3), size=(2 * s, 1.5 * s))
            if n > 1:
                Color(1, 1, 1, .15)
                for k in range(1, n):
                    Line(points=[x + k * ps, y, x + k * ps, y + h], width=1)
                    Line(points=[x, y + k * ps, x + w, y + k * ps], width=1)
            Color(1, 1, 1, .25)
            Line(rectangle=(x, y, w, h), width=1.2)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._t0 = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._t0 and self.on_pick and self.collide_point(*touch.pos):
            if abs(touch.x - self._t0[0]) < dp(12) and abs(touch.y - self._t0[1]) < dp(12):
                ps = self.width / self.grid
                c = int((touch.x - self.x) // ps)
                r = int((self.y + self.height - touch.y) // ps)
                i = max(0, min(self.grid ** 2 - 1, r * self.grid + c))
                if self.pick_all or i not in self.unlocked:
                    self._t0 = None
                    self.on_pick(i)
        self._t0 = None
        return super().on_touch_up(touch)


# ───────────────────────── цветная нонограмма ─────────────────────────
PAPER = (.95, .94, .9)
_PZ = {}


def lum(c):
    return .299 * c[0] + .587 * c[1] + .114 * c[2]


def tcol(c, a=1.0):
    return (1, 1, 1, a) if lum(c) < .55 else (.05, .05, .1, a)


class Puzzle:
    """w x h, pal[i-1] — цвет i (0 = фон/пусто), grid — целевая картинка построчно."""

    def __init__(self, w, h, pal, grid):
        self.w, self.h, self.pal, self.grid = w, h, pal, grid
        self.rows = [self.runs(grid[r * w:(r + 1) * w]) for r in range(h)]
        self.cols = [self.runs(grid[c::w]) for c in range(w)]
        self.total = sum(1 for v in grid if v)
        self.per = [0] * (len(pal) + 1)
        for v in grid:
            if v:
                self.per[v] += 1

    @staticmethod
    def runs(line):
        out, prev, n = [], 0, 0
        for v in line:
            if v and v == prev:
                n += 1
            else:
                if prev:
                    out.append((prev, n))
                prev, n = v, (1 if v else 0)
        if prev:
            out.append((prev, n))
        return out or [(0, 0)]


def kmeans(pts, k, it=8):
    order = sorted(range(len(pts)), key=lambda i: lum(pts[i]))
    cen = [pts[order[int((j + .5) * len(pts) / k)]] for j in range(k)]
    asg = [0] * len(pts)
    for _ in range(it):
        sums = [[0, 0, 0, 0] for _ in range(k)]
        for i, p in enumerate(pts):
            best, bd = 0, 9
            for j, c in enumerate(cen):
                d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                if d < bd:
                    best, bd = j, d
            asg[i] = best
            s = sums[best]
            s[0] += p[0]
            s[1] += p[1]
            s[2] += p[2]
            s[3] += 1
        cen = [(s[0] / s[3], s[1] / s[3], s[2] / s[3]) if s[3] else cen[j] for j, s in enumerate(sums)]
    return cen, asg


def build_puzzle(key, size, ncol, n=1, sector=0):
    """Нонограмма size x size из сектора (sector) картины, поделённой на n x n секторов."""
    ck = (key, size, ncol, n, sector)
    if ck in _PZ:
        return _PZ[ck]
    tex = get_tex(key)
    W, H = tex.size
    pix = tex.pixels  # RGBA, начало внизу слева
    sr, sc = divmod(sector, n)
    x0, y0, sw, sh = sc * W / n, sr * H / n, W / n, H / n  # y0 считается сверху
    pts = []
    for r in range(size):
        for c in range(size):
            rs = gs = bs = 0
            for sy in range(3):
                for sx in range(3):
                    x = min(W - 1, int(x0 + (c + (sx + .5) / 3) * sw / size))
                    y = min(H - 1, H - 1 - int(y0 + (r + (sy + .5) / 3) * sh / size))
                    i = (y * W + x) * 4
                    rs += pix[i]
                    gs += pix[i + 1]
                    bs += pix[i + 2]
            pts.append((rs / 2295.0, gs / 2295.0, bs / 2295.0))
    cen, asg = kmeans(pts, ncol)
    cnt = [0] * ncol
    for a_ in asg:
        cnt[a_] += 1
    bg = max(range(ncol), key=lambda j: cnt[j])
    order = sorted((j for j in range(ncol) if j != bg and cnt[j] > 0), key=lambda j: -cnt[j])
    remap = {bg: 0}
    for k, j in enumerate(order, start=1):
        remap[j] = k
    pz = Puzzle(size, size, [cen[j] for j in order], [remap[a_] for a_ in asg])
    _PZ[ck] = pz
    return pz


class Picross:
    def __init__(self, pz, cells=None):
        self.pz = pz
        n = pz.w * pz.h
        self.cells = list(cells) if cells and len(cells) == n else [-1] * n
        self.undo, self.redo = [], []
        self.correct, self.wrong = 0, 0
        self.left = pz.per[:]
        for i, v in enumerate(self.cells):
            self._count(i, v, 1)
        self.sel, self.tool, self.show_err = 1, "pen", False
        self.celebrated = self.done

    @property
    def done(self):
        return self.correct == self.pz.total and self.wrong == 0

    def _count(self, i, v, sign):
        if v > 0:
            if v == self.pz.grid[i]:
                self.correct += sign
                self.left[v] -= sign
            else:
                self.wrong += sign

    def set(self, i, v, rec):
        old = self.cells[i]
        if old == v:
            return False
        self._count(i, old, -1)
        self.cells[i] = v
        self._count(i, v, 1)
        if rec is not None:
            rec.append((i, old, v))
        return True

    def do_undo(self):
        if self.undo:
            batch = self.undo.pop()
            for i, old, new in reversed(batch):
                self.set(i, old, None)
            self.redo.append(batch)

    def do_redo(self):
        if self.redo:
            batch = self.redo.pop()
            for i, old, new in batch:
                self.set(i, new, None)
            self.undo.append(batch)

    def hint(self):
        pz = self.pz
        miss = [i for i, t in enumerate(pz.grid) if t and self.cells[i] != t]
        rec = []
        if miss:
            i = random.choice(miss)
            self.set(i, pz.grid[i], rec)
        else:
            for i, t in enumerate(pz.grid):
                if not t and self.cells[i] > 0:
                    self.set(i, -1, rec)
        if rec:
            self.undo.append(rec)
            self.redo.clear()

    def line_ok(self, idxs, clue):
        line = [v if v > 0 else 0 for v in (self.cells[i] for i in idxs)]
        return Puzzle.runs(line) == clue

    def row_ok(self, r):
        w = self.pz.w
        return self.line_ok(range(r * w, (r + 1) * w), self.pz.rows[r])

    def col_ok(self, c):
        return self.line_ok(range(c, self.pz.w * self.pz.h, self.pz.w), self.pz.cols[c])


class PicrossBoard(StencilView):
    def __init__(self, g, **kw):
        super().__init__(**kw)
        self.g = g
        pz = g.pz
        self.cell, self.sx, self.sy = dp(26), 0, 0
        self.fitted = False
        self.maxr = max(len(x) for x in pz.rows)
        self.maxc = max(len(x) for x in pz.cols)
        self.on_change = None
        self._cache = {}
        self._mode = None
        self._moving = False
        self._rec = None
        self._last = (0, 0)
        self.prev = Texture.create(size=(pz.w, pz.h), colorfmt="rgb")
        self.prev.mag_filter = self.prev.min_filter = "nearest"
        self._trig = Clock.create_trigger(self.redraw, -1)
        self.bind(pos=self._trig, size=self._on_size)
        self.update_preview()

    def _on_size(self, *a):
        if not self.fitted and self.width > 50 and self.height > 50:
            self.fitted = True
            pz = self.g.pz
            fit = min(self.width / (pz.w + .8 * self.maxr), self.height / (pz.h + .8 * self.maxc))
            self.cell = max(dp(20), min(dp(44), fit))
        self._trig()

    def request_redraw(self):
        self._trig()

    def _geo(self):
        cell = self.cell
        kc = cell * .8
        CW = max(dp(44), self.maxr * kc)
        CH = max(dp(44), self.maxc * kc)
        return cell, kc, CW, CH, self.x + CW, self.top - CH, self.width - CW, self.height - CH

    def _clamp(self):
        cell, kc, CW, CH, gx0, gyt, vw, vh = self._geo()
        pz = self.g.pz
        self.sx = min(max(self.sx, 0), max(0, pz.w * cell - vw))
        self.sy = min(max(self.sy, 0), max(0, pz.h * cell - vh))

    def zoom(self, f):
        old = self.cell
        new = max(dp(14), min(dp(64), old * f))
        if new == old:
            return
        vw, vh = self._geo()[6:8]
        cx, cy = (self.sx + vw / 2) / old, (self.sy + vh / 2) / old
        self.cell = new
        self.sx, self.sy = cx * new - vw / 2, cy * new - vh / 2
        self._cache.clear()
        self._clamp()
        self._trig()

    def update_preview(self):
        pz = self.g.pz
        pal = [tuple(int(x * 255) for x in c) for c in pz.pal]
        bgb = tuple(int(x * 255) for x in PAPER)
        buf = bytearray()
        for r in range(pz.h - 1, -1, -1):
            for c in range(pz.w):
                v = self.g.cells[r * pz.w + c]
                buf += bytes(pal[v - 1] if v > 0 else bgb)
        self.prev.blit_buffer(bytes(buf), colorfmt="rgb", bufferfmt="ubyte")

    def _text(self, t, fs, col, cx, cy):
        k = (t, int(fs), col)
        tx = self._cache.get(k)
        if tx is None:
            l = CoreLabel(text=t, font_size=max(8, int(fs)), color=col)
            l.refresh()
            tx = self._cache[k] = l.texture
        w, h = tx.size
        Color(1, 1, 1, 1)
        Rectangle(texture=tx, pos=(cx - w / 2, cy - h / 2), size=(w, h))

    def redraw(self, *a):
        self.canvas.clear()
        if self.width < 10 or self.height < 10:
            return
        g, pz = self.g, self.g.pz
        self._clamp()
        cell, kc, CW, CH, gx0, gyt, vw, vh = self._geo()
        sx, sy = self.sx, self.sy
        c0, c1 = int(sx // cell), min(pz.w - 1, int((sx + vw) // cell))
        r0, r1 = int(sy // cell), min(pz.h - 1, int((sy + vh) // cell))
        xr = min(self.right, gx0 - sx + pz.w * cell)
        yb = max(self.y, gyt + sy - pz.h * cell)
        with self.canvas:
            Color(*BG)
            Rectangle(pos=self.pos, size=self.size)
            Color(*PAPER)
            Rectangle(pos=(gx0, yb), size=(xr - gx0, gyt - yb))
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    i = r * pz.w + c
                    v = g.cells[i]
                    x, y = gx0 - sx + c * cell, gyt + sy - (r + 1) * cell
                    if v > 0:
                        Color(*pz.pal[v - 1])
                        Rectangle(pos=(x, y), size=(cell, cell))
                        if g.show_err and v != pz.grid[i]:
                            Color(1, .1, .1, .95)
                            Line(points=[x + 3, y + 3, x + cell - 3, y + cell - 3], width=2)
                            Line(points=[x + 3, y + cell - 3, x + cell - 3, y + 3], width=2)
                    elif v == -2:
                        Color(.4, .4, .45, 1)
                        m = cell * .3
                        Line(points=[x + m, y + m, x + cell - m, y + cell - m], width=1.3)
                        Line(points=[x + m, y + cell - m, x + cell - m, y + m], width=1.3)
            for c in range(c0, c1 + 2):
                Color(0, 0, 0, .55 if c % 5 == 0 else .16)
                x = gx0 - sx + c * cell
                Line(points=[x, yb, x, gyt], width=1.5 if c % 5 == 0 else 1)
            for r in range(r0, r1 + 2):
                Color(0, 0, 0, .55 if r % 5 == 0 else .16)
                y = gyt + sy - r * cell
                Line(points=[gx0, y, xr, y], width=1.5 if r % 5 == 0 else 1)
            Color(*PANEL)
            Rectangle(pos=(self.x, gyt), size=(self.width, CH))
            Rectangle(pos=(self.x, self.y), size=(CW, vh))
            for c in range(c0, c1 + 1):
                runs = pz.cols[c]
                a = .3 if g.col_ok(c) else 1
                x = gx0 - sx + c * cell
                for i, (col, n) in enumerate(runs):
                    y = gyt + (len(runs) - 1 - i) * kc
                    cc = pz.pal[col - 1] if col else (.35, .37, .45)
                    Color(*cc, a)
                    Rectangle(pos=(x + 1, y + 1), size=(cell - 2, kc - 2))
                    self._text(str(n), kc * .62, tcol(cc, a), x + cell / 2, y + kc / 2)
            for r in range(r0, r1 + 1):
                runs = pz.rows[r]
                a = .3 if g.row_ok(r) else 1
                y = gyt + sy - (r + 1) * cell
                for i, (col, n) in enumerate(runs):
                    x = gx0 - (len(runs) - i) * kc
                    cc = pz.pal[col - 1] if col else (.35, .37, .45)
                    Color(*cc, a)
                    Rectangle(pos=(x + 1, y + 1), size=(kc - 2, cell - 2))
                    self._text(str(n), kc * .62, tcol(cc, a), x + kc / 2, y + cell / 2)
            Color(*PANEL)
            Rectangle(pos=(self.x, gyt), size=(CW, CH))
            s = min(CW, CH) - dp(6)
            Color(1, 1, 1, 1)
            Rectangle(texture=self.prev, pos=(self.x + (CW - s) / 2, gyt + (CH - s) / 2), size=(s, s))

    def cell_at(self, x, y):
        cell, kc, CW, CH, gx0, gyt, vw, vh = self._geo()
        pz = self.g.pz
        if x < gx0 or y > gyt or x > self.right or y < self.y:
            return -1
        c, r = int((x - gx0 + self.sx) // cell), int((gyt - y + self.sy) // cell)
        return r * pz.w + c if 0 <= c < pz.w and 0 <= r < pz.h else -1

    def _apply(self, i):
        g, v, m = self.g, self.g.cells[i], self._mode
        if m == "paint":
            g.set(i, g.sel, self._rec)
        elif m == "erase" and v == g.sel:
            g.set(i, -1, self._rec)
        elif m == "xon" and v == -1:
            g.set(i, -2, self._rec)
        elif m == "xoff" and v == -2:
            g.set(i, -1, self._rec)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        g = self.g
        touch.grab(self)
        self._last = touch.pos
        self._mode, self._rec = None, None
        self._moving = g.tool == "move"
        if self._moving:
            return True
        i = self.cell_at(*touch.pos)
        if i >= 0:
            v = g.cells[i]
            if g.tool == "pen":
                self._mode = "erase" if v == g.sel else "paint"
            else:
                self._mode = "xoff" if v == -2 else "xon"
            self._rec = []
            self._apply(i)
            self._trig()
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if self._moving:
            self.sx -= touch.dx
            self.sy += touch.dy
            self._clamp()
            self._trig()
        elif self._mode:
            x0, y0 = self._last
            x1, y1 = touch.pos
            steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) // (self.cell / 2)))
            for s in range(1, steps + 1):
                i = self.cell_at(x0 + (x1 - x0) * s / steps, y0 + (y1 - y0) * s / steps)
                if i >= 0:
                    self._apply(i)
            self._last = touch.pos
            self._trig()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if self._mode and self._rec:
            self.g.undo.append(self._rec)
            self.g.redo.clear()
        self._mode, self._rec = None, None
        if self.on_change:
            self.on_change(True)
        return True


class Swatch(BoxLayout):
    def __init__(self, color, on_tap, **kw):
        super().__init__(padding=dp(3), **kw)
        with self.canvas.before:
            self._bc = Color(1, 1, 1, 0)
            self._br = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._u, size=self._u)
        self.btn = RBtn("", bg=(*color, 1), fg=tcol(color), radius=9, font_size=sp(14))
        self.btn.bind(on_release=lambda *_: on_tap())
        self.add_widget(self.btn)

    def _u(self, *a):
        self._br.pos, self._br.size = self.pos, self.size

    def mark(self, sel):
        self._bc.rgba = (1, 1, 1, 1 if sel else 0)


class GameScreen(Screen):
    def start(self, g, pic, skey, sector=0, n=1):
        self.g, self.pic, self.skey, self.sector = g, pic, skey, sector
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        self.add_widget(root)
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        top.add_widget(RBtn("<", size_hint_x=None, width=dp(44),
                            on_release=lambda *_: MDApp.get_running_app().go_home()))
        top.add_widget(lab("%s · часть %d/%d" % (pic["title"], sector + 1, n * n), 15, TXT, True, align="left"))
        self.pct = lab("0%", 17, GOLD, True)
        self.pct.size_hint_x = None
        self.pct.width = dp(60)
        top.add_widget(self.pct)
        root.add_widget(top)
        self.board = PicrossBoard(g)
        self.board.on_change = self.changed
        root.add_widget(self.board)
        pal = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(2))
        self.sw = {}
        for i, col in enumerate(g.pz.pal, start=1):
            s = Swatch(col, lambda i=i: self.pick(i))
            self.sw[i] = s
            pal.add_widget(s)
        root.add_widget(pal)
        r1 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.tb = {}
        for key, name in (("pen", "Кисть"), ("x", "Крестик"), ("move", "Рука")):
            b = RBtn(name)
            b.bind(on_release=lambda *_, k=key: self.set_tool(k))
            self.tb[key] = b
            r1.add_widget(b)
        for name, cb in (("Отмена", self.do_undo), ("Повтор", self.do_redo)):
            b = RBtn(name)
            b.bind(on_release=lambda *_, f=cb: f())
            r1.add_widget(b)
        root.add_widget(r1)
        r2 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.err_btn = RBtn("Ошибки")
        for name, cb in (("  -  ", lambda: self.board.zoom(1 / 1.25)), ("  +  ", lambda: self.board.zoom(1.25)),
                         ("Подсказка", self.do_hint), (None, self.do_err)):
            b = self.err_btn if name is None else RBtn(name)
            b.bind(on_release=lambda *_, f=cb: f())
            r2.add_widget(b)
        root.add_widget(r2)
        self.changed(False)

    def pick(self, i):
        self.g.sel = i
        if self.g.tool == "move":
            self.g.tool = "pen"
        self.changed(False)

    def set_tool(self, k):
        self.g.tool = k
        self.changed(False)

    def do_undo(self):
        self.g.do_undo()
        self.changed(True)

    def do_redo(self):
        self.g.do_redo()
        self.changed(True)

    def do_hint(self):
        self.g.hint()
        self.changed(True)

    def do_err(self):
        self.g.show_err = not self.g.show_err
        self.changed(False)

    def changed(self, final=True):
        g = self.g
        self.pct.text = "%d%%" % (100 * g.correct // max(1, g.pz.total))
        for i, s in self.sw.items():
            s.btn.text = str(g.left[i]) if g.left[i] > 0 else ""
            s.btn.opacity = 1 if g.left[i] > 0 else .4
            s.mark(i == g.sel)
        for k, b in self.tb.items():
            b.set_bg(SELC if g.tool == k else PANEL2)
        self.err_btn.set_bg(SELC if g.show_err else PANEL2)
        self.board.update_preview()
        self.board.request_redraw()
        if final:
            app = MDApp.get_running_app()
            app.save_progress(self.skey, g)
            if g.done and not g.celebrated:
                g.celebrated = True
                app.on_win(self.pic, self.sector)


class HomeScreen(Screen):
    PAGE = 6

    def __init__(self, **kw):
        super().__init__(**kw)
        self.cat, self.page = "Все", 0
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        self.add_widget(root)
        root.add_widget(lab("Цветные нонограммы", 26, GOLD, True, h=44))
        self.sub = lab("", 14, MUTED, h=22)
        root.add_widget(self.sub)
        drow = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.dbtn = []
        for i, (name, n, _, k) in enumerate(DIFFS):
            b = RBtn("%s\n%dx%d" % (name, n * k, n * k), font_size=sp(13))
            b.bind(on_release=lambda *_, k=i: self.set_diff(k))
            self.dbtn.append(b)
            drow.add_widget(b)
        root.add_widget(drow)
        self.chips_sv = ScrollView(size_hint_y=None, height=dp(44), do_scroll_y=False)
        self.chips = BoxLayout(size_hint_x=None, spacing=dp(8))
        self.chips.bind(minimum_width=self.chips.setter("width"))
        self.chips_sv.add_widget(self.chips)
        root.add_widget(self.chips_sv)
        self.scroll = ScrollView(do_scroll_x=False)
        root.add_widget(self.scroll)

    def set_diff(self, k):
        app = MDApp.get_running_app()
        app.data["diff"] = k
        app.save()
        self.refresh()

    def set_cat(self, c):
        self.cat, self.page = c, 0
        self.refresh()

    def go_page(self, d):
        self.page += d
        self.refresh()

    def _nav(self, pages):
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        a = RBtn("‹ Назад", opacity=1 if self.page > 0 else .3)
        b = RBtn("Дальше ›", opacity=1 if self.page < pages - 1 else .3)
        a.bind(on_release=lambda *_: self.page > 0 and self.go_page(-1))
        b.bind(on_release=lambda *_: self.page < pages - 1 and self.go_page(1))
        row.add_widget(a)
        row.add_widget(lab("%d / %d" % (self.page + 1, pages), 15, MUTED))
        row.add_widget(b)
        return row

    def refresh(self):
        app = MDApp.get_running_app()
        d = app.data
        di = d["diff"]
        for i, b in enumerate(self.dbtn):
            b.set_bg(SELC if i == di else PANEL2)
        k = DIFFS[di][3]
        done = sum(1 for p in PICS if len(app.done_sectors(p["id"])) == k * k)
        self.sub.text = "Собрано картин: %d из %d   (секторов в картине: %d)" % (done, len(PICS), k * k)
        self.chips.clear_widgets()
        for c in CATS:
            self.chips.add_widget(RBtn(c, bg=SELC if c == self.cat else PANEL2, size_hint_x=None,
                                       width=dp(30) + dp(10) * len(c),
                                       on_release=lambda *_, c=c: self.set_cat(c)))
        self.scroll.clear_widgets()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14), padding=[0, dp(6), 0, dp(20)])
        box.bind(minimum_height=box.setter("height"))
        items = [p for p in PICS if self.cat == "Все" or p["cat"] == self.cat]
        pages = max(1, -(-len(items) // self.PAGE))
        self.page = min(self.page, pages - 1)
        for p in items[self.page * self.PAGE:(self.page + 1) * self.PAGE]:
            ds = app.done_sectors(p["id"])
            status = "собрана" if len(ds) == k * k else "%d/%d" % (len(ds), k * k)
            card = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(lab("%s   %s" % (p["title"], status), 17, TXT, True, h=28, align="left"))
            if p["author"]:
                card.add_widget(lab(p["author"][:70], 12, MUTED, h=18, align="left"))
            pv = PictureView(("p", p["id"]), k, ds, size_hint=(1, None),
                             on_pick=lambda i, p=p: app.open_puzzle(p, i))
            pv.ghost = .35
            pv.bind(width=lambda w, v: setattr(w, "height", v))
            card.add_widget(pv)
            box.add_widget(card)
        if pages > 1:
            box.add_widget(self._nav(pages))
        self.scroll.add_widget(box)


class PicrossApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        Window.clearcolor = BG
        self.data = self.load()
        self.sm = ScreenManager(transition=FadeTransition(duration=.15))
        self.home = HomeScreen(name="home")
        self.gs = GameScreen(name="game")
        self.sm.add_widget(self.home)
        self.sm.add_widget(self.gs)
        Window.bind(on_keyboard=self.on_key)
        Clock.schedule_once(lambda dt: self.home.refresh(), 0)
        return self.sm

    def _path(self):
        return os.path.join(self.user_data_dir, "save.json")

    def load(self):
        d = {"saves": {}, "diff": 0}
        try:
            with open(self._path(), encoding="utf-8") as f:
                d.update(json.load(f))
        except Exception:
            pass
        return d

    def save(self):
        try:
            with open(self._path(), "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception:
            pass

    def save_progress(self, skey, g):
        self.data["saves"][skey] = {"cells": g.cells, "done": g.done,
                                    "pct": 100 * g.correct // max(1, g.pz.total)}
        self.save()

    def on_key(self, win, key, *a):
        if key == 27 and self.sm.current == "game":
            self.go_home()
            return True
        return False

    def go_home(self):
        self.sm.current = "home"
        self.home.refresh()

    def done_sectors(self, pid):
        di = self.data["diff"]
        k = DIFFS[di][3]
        sv = self.data["saves"]
        return [i for i in range(k * k) if sv.get("%s|%d|%d" % (pid, di, i), {}).get("done")]

    def open_puzzle(self, p, sector):
        di = self.data["diff"]
        _, size, ncol, k = DIFFS[di]
        skey = "%s|%d|%d" % (p["id"], di, sector)
        busy = ModalView(size_hint=(.7, None), height=dp(90), auto_dismiss=False, background_color=(0, 0, 0, .6))
        busy.add_widget(lab("Готовлю головоломку…", 18))
        busy.open()

        def go(dt):
            pz = build_puzzle(("p", p["id"]), size, ncol, k, sector)
            g = Picross(pz, self.data["saves"].get(skey, {}).get("cells"))
            busy.dismiss()
            self.gs.start(g, p, skey, sector, k)
            self.sm.current = "game"

        Clock.schedule_once(go, .2)

    def on_win(self, pic, sector):
        k = DIFFS[self.data["diff"]][3]
        done = self.done_sectors(pic["id"])
        full = len(done) >= k * k
        mv = ModalView(size_hint=(.94, None), height=dp(150) + min(Window.width * .86, Window.height * .5),
                       auto_dismiss=False, background_color=(0, 0, 0, .75))
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(lab("Картина собрана!" if full else "Открыта часть: %d из %d" % (len(done), k * k), 22, GOLD, True, h=40))
        side = min(Window.width * .86, Window.height * .5)
        anchor = AnchorLayout()
        pv = PictureView(("p", pic["id"]), k, done, size_hint=(None, None), size=(side, side))
        anchor.add_widget(pv)
        box.add_widget(anchor)
        b = RBtn("К галерее" if full else "Дальше", bg=SELC, size_hint_y=None, height=dp(52), font_size=sp(18))
        b.bind(on_release=lambda *_: (mv.dismiss(), self.go_home()))
        box.add_widget(b)
        mv.add_widget(box)
        mv.open()
        pv.fresh, pv.fresh_a = sector, 0
        Animation(fresh_a=1, d=1.6, t="out_quad").start(pv)


if __name__ == "__main__":
    PicrossApp().run()
