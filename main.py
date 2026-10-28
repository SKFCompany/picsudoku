import colorsys
import json
import os
import random
import threading
import time

from kivy.animation import Animation
from kivy.clock import Clock, mainthread
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
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivymd.app import MDApp

from scenes2 import SCENES2
from sudoku import Sudoku

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

DIFFS = [("Легко", 6, 1), ("Средне", 9, 0), ("Сложно", 9, 2)]  # название, размер, уровень
MAX_MISTAKES = 3

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
STICKERS = [dict(id="m%d" % k, src=sc_mandala(k)) for k in range(24)] + _fs
PIC_BY_ID = {p["id"]: p for p in PICS}
ST_BY_ID = {s["id"]: s for s in STICKERS}
CATS = ["Все"] + list(dict.fromkeys(p["cat"] for p in PICS))

_TEX, _FBO, _REG = {}, {}, {}
_CAP = {"p": 18, "s": 60}


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
            Color(1, 1, 1, .2)
            Rectangle(texture=tex, pos=(x, y), size=(w, h))
            for i in range(n * n):
                r, c = divmod(i, n)
                p = (x + c * ps, y + h - (r + 1) * ps)
                if i in self.unlocked:
                    Color(1, 1, 1, self.fresh_a if i == self.fresh else 1)
                    Rectangle(texture=get_region(self.key, n, i), pos=p, size=(ps, ps))
                else:
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
                if i not in self.unlocked:
                    self._t0 = None
                    self.on_pick(i)
        self._t0 = None
        return super().on_touch_up(touch)


# ───────────────────────── игра ─────────────────────────
class Game:
    def __init__(self, n, level):
        self.n = n
        self.sd = Sudoku(n)
        self.br, self.bc = self.sd.br, self.sd.bc
        self.puz, self.sol = self.sd.make(level)
        self.g = self.puz[:]
        self.given = [v != 0 for v in self.puz]
        self.notes = [set() for _ in range(n * n)]
        self.sel = -1
        self.mist = 0
        self.hints = 3
        self.undo = []
        self.notes_mode = False
        self.done = False
        self.lost = False
        self.t0 = time.time()

    def box(self, i):
        return self.sd.box(i)

    def select(self, i):
        self.sel = i

    def _push(self, i):
        self.undo.append((i, self.g[i], set(self.notes[i])))

    def _clean_peers(self, i, d):
        for p in self.sd.peers[i]:
            self.notes[p].discard(d)

    def put(self, d):
        i = self.sel
        if i < 0 or self.given[i] or self.done:
            return
        if self.notes_mode:
            if self.g[i]:
                return
            self._push(i)
            if d in self.notes[i]:
                self.notes[i].discard(d)
            else:
                self.notes[i].add(d)
            return
        if self.g[i] == d:
            return
        self._push(i)
        self.g[i] = d
        self.notes[i] = set()
        if d != self.sol[i]:
            self.mist += 1
            if self.mist >= MAX_MISTAKES:
                self.done = self.lost = True
        else:
            self._clean_peers(i, d)
            self.check()

    def erase(self):
        i = self.sel
        if i < 0 or self.given[i] or self.done:
            return
        self._push(i)
        self.g[i] = 0
        self.notes[i] = set()

    def back(self):
        if self.undo and not self.done:
            i, v, nt = self.undo.pop()
            self.g[i], self.notes[i] = v, nt
            self.sel = i

    def hint(self):
        if self.hints <= 0 or self.done:
            return
        i = self.sel
        if i < 0 or self.given[i] or self.g[i] == self.sol[i]:
            bad = [k for k in range(self.n ** 2) if self.g[k] != self.sol[k]]
            if not bad:
                return
            i = bad[0]
            self.sel = i
        self._push(i)
        self.g[i] = self.sol[i]
        self.notes[i] = set()
        self._clean_peers(i, self.sol[i])
        self.hints -= 1
        self.check()

    def check(self):
        if self.g == self.sol:
            self.done = True

    @property
    def won(self):
        return self.done and not self.lost

    def placed(self, d):
        return sum(1 for i in range(self.n ** 2) if self.g[i] == d and self.sol[i] == d)


class Board(Widget):
    def __init__(self, game, **kw):
        super().__init__(**kw)
        self.game = game
        self._cache = {}
        self.on_select = None
        self.bind(pos=self.redraw, size=self.redraw)

    def _tex(self, t, fs, col):
        k = (t, fs, col)
        if k not in self._cache:
            l = CoreLabel(text=t, font_size=fs, color=col)
            l.refresh()
            self._cache[k] = l.texture
        return self._cache[k]

    def _text(self, t, fs, col, cx, cy):
        tx = self._tex(t, max(8, int(fs)), col)
        w, h = tx.size
        Color(1, 1, 1, 1)
        Rectangle(texture=tx, pos=(cx - w / 2, cy - h / 2), size=(w, h))

    def _geom(self):
        s = min(self.width, self.height)
        return self.x + (self.width - s) / 2, self.y + (self.height - s) / 2, s

    def redraw(self, *a):
        g = self.game
        n = g.n
        ox, oy, s = self._geom()
        cs = s / n
        self.canvas.clear()
        with self.canvas:
            Color(*PANEL)
            RoundedRectangle(pos=(ox - dp(4), oy - dp(4)), size=(s + dp(8), s + dp(8)), radius=[dp(14)])
            if g.sel >= 0:
                sr, sc = divmod(g.sel, n)
                sv = g.g[g.sel]
                for i in range(n * n):
                    r, c = divmod(i, n)
                    col = None
                    if i == g.sel:
                        col = SELC
                    elif sv and g.g[i] == sv:
                        col = SAME
                    elif r == sr or c == sc or g.box(i) == g.box(g.sel):
                        col = HL
                    if col:
                        Color(*col)
                        Rectangle(pos=(ox + c * cs + 1, oy + s - (r + 1) * cs + 1), size=(cs - 2, cs - 2))
            for k in range(1, n):
                for vertical in (True, False):
                    thick = (k % g.bc == 0) if vertical else (k % g.br == 0)
                    Color(*((.65, .75, 1, .7) if thick else (1, 1, 1, .1)))
                    w = 2.2 if thick else 1
                    if vertical:
                        Line(points=[ox + k * cs, oy, ox + k * cs, oy + s], width=w)
                    else:
                        Line(points=[ox, oy + k * cs, ox + s, oy + k * cs], width=w)
            for i in range(n * n):
                r, c = divmod(i, n)
                v = g.g[i]
                if v:
                    col = TXT if g.given[i] else (RED if v != g.sol[i] else ACC)
                    self._text(str(v), cs * .56, col, ox + (c + .5) * cs, oy + s - (r + .5) * cs)
                elif g.notes[i]:
                    for d in g.notes[i]:
                        rr, cc = divmod(d - 1, g.bc)
                        self._text(str(d), cs * .24, MUTED,
                                   ox + c * cs + (cc + .5) * cs / g.bc,
                                   oy + s - r * cs - (rr + .5) * cs / g.br)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            ox, oy, s = self._geom()
            n = self.game.n
            cs = s / n
            c = int((touch.x - ox) // cs)
            r = int((oy + s - touch.y) // cs)
            if 0 <= r < n and 0 <= c < n:
                self.game.select(r * n + c)
                if self.on_select:
                    self.on_select()
                return True
        return super().on_touch_down(touch)


class GameScreen(Screen):
    def start(self, game, reward, title):
        self.game, self.reward = game, reward
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        self.add_widget(root)
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        top.add_widget(RBtn("<", size_hint_x=None, width=dp(46),
                            on_release=lambda *_: MDApp.get_running_app().go_home()))
        top.add_widget(lab(title, 17, TXT, True, align="left"))
        self.timer = lab("00:00", 17, GOLD, True)
        self.timer.size_hint_x = None
        self.timer.width = dp(70)
        top.add_widget(self.timer)
        root.add_widget(top)
        self.board = Board(game, size_hint=(1, None))
        self.board.bind(width=lambda w, v: setattr(w, "height", v))
        self.board.on_select = self.refresh
        root.add_widget(self.board)
        self.stats = lab("", 14, MUTED, h=26)
        root.add_widget(self.stats)
        acts = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.btn_notes = RBtn("Заметки")
        for name, cb in (("Отмена", self.do_undo), ("Стереть", self.do_erase),
                         (None, self.do_notes), ("Подсказка", self.do_hint)):
            b = self.btn_notes if name is None else RBtn(name)
            b.bind(on_release=lambda *_, f=cb: f())
            acts.add_widget(b)
        root.add_widget(acts)
        pad = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        self.pad = {}
        for d in range(1, game.n + 1):
            b = RBtn(str(d), bg=PANEL, fg=ACC, font_size=sp(24), radius=10)
            b.bind(on_release=lambda *_, k=d: self.digit(k))
            self.pad[d] = b
            pad.add_widget(b)
        root.add_widget(pad)
        root.add_widget(Widget())
        self.refresh()
        self._ev = Clock.schedule_interval(self.tick, 1)

    def stop(self):
        ev = getattr(self, "_ev", None)
        if ev:
            ev.cancel()
            self._ev = None

    def tick(self, dt):
        if not self.game.done:
            t = int(time.time() - self.game.t0)
            self.timer.text = "%02d:%02d" % (t // 60, t % 60)

    def digit(self, d):
        self.game.put(d)
        self.after()

    def do_undo(self):
        self.game.back()
        self.after()

    def do_erase(self):
        self.game.erase()
        self.after()

    def do_hint(self):
        self.game.hint()
        self.after()

    def do_notes(self):
        self.game.notes_mode = not self.game.notes_mode
        self.refresh()

    def after(self):
        self.refresh()
        g = self.game
        if g.done:
            self.stop()
            if g.won:
                MDApp.get_running_app().on_win(self.reward, int(time.time() - g.t0))
            else:
                MDApp.get_running_app().on_lose()

    def refresh(self):
        g = self.game
        self.board.redraw()
        self.stats.text = "Ошибки: %d/%d      Подсказки: %d" % (g.mist, MAX_MISTAKES, g.hints)
        self.btn_notes.set_bg(SELC if g.notes_mode else PANEL2)
        self.btn_notes.text = "Заметки: вкл" if g.notes_mode else "Заметки"
        for d, b in self.pad.items():
            full = g.placed(d) >= g.n
            b.opacity = .3 if full else 1
            b.disabled = full


class HomeScreen(Screen):
    PAGE_P, PAGE_S = 6, 12

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tab, self.cat, self.page = "p", "Все", 0
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        self.add_widget(root)
        root.add_widget(lab("Судоку-Галерея", 26, GOLD, True, h=44))
        self.sub = lab("", 14, MUTED, h=22)
        root.add_widget(self.sub)
        drow = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.dbtn = []
        for i, (name, _, _) in enumerate(DIFFS):
            b = RBtn(name)
            b.bind(on_release=lambda *_, k=i: self.set_diff(k))
            self.dbtn.append(b)
            drow.add_widget(b)
        root.add_widget(drow)
        trow = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.tbtn = {}
        for k, name in (("p", "Картины"), ("s", "Стикеры")):
            b = RBtn(name, font_size=sp(17))
            b.bind(on_release=lambda *_, t=k: self.set_tab(t))
            self.tbtn[k] = b
            trow.add_widget(b)
        root.add_widget(trow)
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

    def set_tab(self, t):
        self.tab, self.page = t, 0
        self.refresh()

    def set_cat(self, c):
        self.cat, self.page = c, 0
        self.refresh()

    def go_page(self, delta):
        self.page += delta
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
        for i, b in enumerate(self.dbtn):
            b.set_bg(SELC if i == d["diff"] else PANEL2)
        for k, b in self.tbtn.items():
            b.set_bg(SELC if k == self.tab else PANEL2)
        total = sum(len(d["pieces"].get(p["id"], [])) for p in PICS)
        self.sub.text = "Частей: %d/%d    Стикеров: %d/%d" % (
            total, len(PICS) * 9, sum(1 for s in STICKERS if s["id"] in d["stickers"]), len(STICKERS))
        show = self.tab == "p"
        self.chips_sv.height = dp(44) if show else 0
        self.chips_sv.opacity = 1 if show else 0
        self.chips.clear_widgets()
        if show:
            for c in CATS:
                self.chips.add_widget(RBtn(c, bg=SELC if c == self.cat else PANEL2, size_hint_x=None,
                                           width=dp(30) + dp(10) * len(c),
                                           on_release=lambda *_, c=c: self.set_cat(c)))
        self.scroll.clear_widgets()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14), padding=[0, dp(6), 0, dp(20)])
        box.bind(minimum_height=box.setter("height"))
        if show:
            items = [p for p in PICS if self.cat == "Все" or p["cat"] == self.cat]
            pages = max(1, -(-len(items) // self.PAGE_P))
            self.page = min(self.page, pages - 1)
            _, n, lvl = DIFFS[d["diff"]]
            for p in items[self.page * self.PAGE_P:(self.page + 1) * self.PAGE_P]:
                have = d["pieces"].get(p["id"], [])
                card = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
                card.bind(minimum_height=card.setter("height"))
                card.add_widget(lab("%s   %d/9" % (p["title"], len(have)), 17, TXT, True, h=28, align="left"))
                if p["author"]:
                    card.add_widget(lab(p["author"][:70], 12, MUTED, h=18, align="left"))
                pv = PictureView(("p", p["id"]), 3, have, size_hint=(1, None),
                                 on_pick=lambda i, p=p: app.begin(("p", p["id"], i), n, lvl,
                                                                  "%s · часть %d" % (p["title"], i + 1)))
                pv.bind(width=lambda w, v: setattr(w, "height", v))
                card.add_widget(pv)
                box.add_widget(card)
        else:
            pages = max(1, -(-len(STICKERS) // self.PAGE_S))
            self.page = min(self.page, pages - 1)
            grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(10))
            grid.bind(minimum_height=grid.setter("height"))
            for gi in range(self.page * self.PAGE_S, min(len(STICKERS), (self.page + 1) * self.PAGE_S)):
                s = STICKERS[gi]
                n, lvl = (4, 0) if gi < 4 else ((6, 0) if gi < 10 else (6, 1))
                pv = PictureView(("s", s["id"]), 1, [0] if s["id"] in d["stickers"] else [],
                                 size_hint_y=None,
                                 on_pick=lambda i, s=s, n=n, lvl=lvl, gi=gi: app.begin(
                                     ("s", s["id"]), n, lvl, "Стикер %d" % (gi + 1)))
                pv.bind(width=lambda w, v: setattr(w, "height", v))
                grid.add_widget(pv)
            box.add_widget(grid)
        if pages > 1:
            box.add_widget(self._nav(pages))
        self.scroll.add_widget(box)


class PicSudokuApp(MDApp):
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

    # --- сохранение ---
    def _path(self):
        return os.path.join(self.user_data_dir, "save.json")

    def load(self):
        d = {"pieces": {}, "stickers": [], "diff": 0}
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

    # --- навигация ---
    def on_key(self, win, key, *a):
        if key == 27 and self.sm.current == "game":
            self.go_home()
            return True
        return False

    def go_home(self):
        self.gs.stop()
        self.sm.current = "home"
        self.home.refresh()

    def begin(self, reward, n, level, title):
        busy = ModalView(size_hint=(.7, None), height=dp(90), auto_dismiss=False,
                         background_color=(0, 0, 0, .6))
        busy.add_widget(lab("Создаю головоломку…", 18))
        busy.open()

        def work():
            g = Game(n, level)
            self._launch(busy, g, reward, title)

        threading.Thread(target=work, daemon=True).start()

    @mainthread
    def _launch(self, busy, g, reward, title):
        busy.dismiss()
        self.gs.start(g, reward, title)
        self.sm.current = "game"

    # --- итоги ---
    def _overlay(self, head, key, grid, unlocked, fresh, btn_text, cb):
        mv = ModalView(size_hint=(.94, None), height=dp(150) + min(Window.width * .86, Window.height * .5),
                       auto_dismiss=False, background_color=(0, 0, 0, .75))
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(lab(head, 22, GOLD, True, h=40))
        side = min(Window.width * .86, Window.height * .5)
        anchor = AnchorLayout()
        pv = PictureView(key, grid, unlocked, size_hint=(None, None), size=(side, side))
        anchor.add_widget(pv)
        box.add_widget(anchor)
        b = RBtn(btn_text, bg=SELC, size_hint_y=None, height=dp(52), font_size=sp(18))
        b.bind(on_release=lambda *_: (mv.dismiss(), cb()))
        box.add_widget(b)
        mv.add_widget(box)
        mv.open()
        if fresh >= 0:
            pv.fresh, pv.fresh_a = fresh, 0
            Animation(fresh_a=1, d=1.5, t="out_quad").start(pv)

    def on_win(self, reward, secs):
        if reward[0] == "p":
            _, pi, piece = reward
            lst = self.data["pieces"].setdefault(str(pi), [])
            if piece not in lst:
                lst.append(piece)
            self.save()
            full = len(lst) >= 9
            head = "Картина собрана!" if full else "Открыта новая часть!"
            self._overlay(head, ("p", pi), 3, lst, piece, "Дальше", self.go_home)
        else:
            si = reward[1]
            if si not in self.data["stickers"]:
                self.data["stickers"].append(si)
            self.save()
            self._overlay("Стикер получен!", ("s", si), 1, [0], 0, "Дальше", self.go_home)

    def on_lose(self):
        mv = ModalView(size_hint=(.85, None), height=dp(190), auto_dismiss=False,
                       background_color=(0, 0, 0, .75))
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        box.add_widget(lab("Слишком много ошибок", 20, RED, True, h=40))
        box.add_widget(lab("Не страшно — попробуй ещё раз с новой сеткой.", 15, MUTED))
        b = RBtn("К галерее", bg=SELC, size_hint_y=None, height=dp(50))
        b.bind(on_release=lambda *_: (mv.dismiss(), self.go_home()))
        box.add_widget(b)
        mv.add_widget(box)
        mv.open()


if __name__ == "__main__":
    PicSudokuApp().run()
