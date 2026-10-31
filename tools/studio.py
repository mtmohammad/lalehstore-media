"""lalehstore STUDIO renderer: the light story look + cinematic motion + 3D products.

Same JSON spec as cinema.py / collage.py (hook / steps / outro / music / seed / format).

Look (same as the daily story, story.py): light background with soft pink/blue glows, the
lalehstore lockup, brand-gradient pills, white rounded cards, Vazirmatn type.
Motion (kept from cinema.py): word-by-word kinetic typography (right to left), eased entrances,
slow camera push with parallax, and a full-screen torn-paper wipe between scenes (the sheets are
now white / brand gradient / soft pink / soft blue with the logo).
3D products: each product photo becomes a 3D relief model. A monocular depth map (MiDaS small,
ONNX, downloaded once from the MiDaS GitHub release; a geometric dome is used if that fails) gives
every pixel a depth, the edge gets a side wall (thickness), and the model is rendered with real
perspective while it turns (yaw/pitch spring in, then a slow turntable sway), lit by a moving key
light with a specular sweep, with a floor reflection and a contact shadow. Nothing is invented:
the surface is the store's own photo.

Usage:
  python3 -I studio.py spec.json out.mp4 [--preview DIR]
"""
import json
import math
import os
import random
import subprocess
import sys
import urllib.request
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collage as cl  # noqa: E402
import make_post as mp  # noqa: E402
from collage import paper_texture, torn_mask  # noqa: E402
from make_wa import BLUE, PINK  # noqa: E402

mp.FONT_DIR = str(HERE / "fonts")
mp.LATIN_FONT = str(HERE / "fonts" / "quicksand-latin-700-normal.woff")

FPS = 30
W, H = 1080, 1920
WIPE = 0.36
BG = (246, 247, 251)
INK = (28, 30, 42)
MUTED = (110, 114, 132)
WHITE = (255, 255, 255)
SOFT_PINK = (253, 226, 235)
SOFT_BLUE = (222, 236, 255)
PHONE, SITE = "021-33917554", "lalehstore.com"
SS = 2
MIDAS_URL = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"
CACHE = Path(os.environ.get("LALEH_CACHE", Path.home() / ".cache" / "lalehstore"))


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def pr(t, a, d):
    return clamp((t - a) / d) if d > 0 else (1.0 if t >= a else 0.0)


def out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_out_cubic(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.6):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def spring(x, k=7.0, z=0.42):
    """Damped spring 0→1 (overshoots a little, settles)."""
    x = max(0.0, x)
    return 1 - math.exp(-z * k * x) * math.cos(k * math.sqrt(1 - z * z) * x)


def is_fa(s):
    return any("؀" <= ch <= "ۿ" for ch in s)


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


def blur_rgba(im, r):
    return im.convert("RGBa").filter(ImageFilter.GaussianBlur(r)).convert("RGBA")


# ------------------------------------------------------------------ type
def word_img(word, px, color, weight="Black"):
    f = mp.font(weight, px * SS)
    hh = int(px * 2.4 * SS)
    ww = int(len(word) * px * SS * 1.2 + 4 * px * SS)
    layer = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((ww // 2, int(px * 1.6 * SS)), word, font=f, fill=(0, 0, 0, 255),
                               anchor="ms", direction="rtl" if is_fa(word) else "ltr")
    bb = layer.getchannel("A").getbbox()
    layer = layer.crop((bb[0], 0, bb[2], hh))
    layer = layer.resize((max(1, layer.width // SS), hh // SS), Image.LANCZOS)
    return layer.getchannel("A")


def chunks(text):
    out = []
    for tok in text.split():
        if out and not is_fa(tok) and not is_fa(out[-1]):
            out[-1] += " " + tok
        else:
            out.append(tok)
    return out


class KText:
    """Kinetic line(s): words rise and settle one by one, right to left. color = rgb or "grad"."""

    def __init__(self, text, px, color=INK, weight="Black", max_w=None, lines=2):
        max_w = max_w or W - 120
        parts = chunks(text)
        while True:
            masks = [word_img(p, px, color, weight) for p in parts]
            gap = int(px * 0.28)
            rows, cur, cw = [], [], 0
            for m in masks:
                if cur and cw + gap + m.width > max_w:
                    rows.append(cur)
                    cur, cw = [], 0
                cw += (gap if cur else 0) + m.width
                cur.append(m)
            rows.append(cur)
            if (len(rows) <= lines and all(m.width <= max_w for m in masks)) or px <= 26:
                break
            px = int(px * 0.92)
        top = min(m.getbbox()[1] for m in masks)
        bot = max(m.getbbox()[3] for m in masks)
        lh = bot - top
        lead = int(lh * 0.22)
        widths = [sum(m.width for m in r) + gap * (len(r) - 1) for r in rows]
        self.w = max(widths)
        self.h = lh * len(rows) + lead * (len(rows) - 1)
        if color == "grad":
            fill = mp.brand_gradient(self.w, self.h)
        else:
            fill = Image.new("RGBA", (self.w, self.h), tuple(color) + (255,))
        self.words = []
        y = 0
        for r, rw in zip(rows, widths):
            x = self.w - (self.w - rw) // 2      # centred block, RTL fill
            for m in r:
                x -= m.width
                a = Image.new("L", (self.w, self.h), 0)
                a.paste(m.crop((0, top, m.width, bot)), (x, y))
                bb = (x, y, x + m.width, y + lh)
                piece = fill.crop(bb)
                piece.putalpha(a.crop(bb))
                self.words.append((piece, x, y))
                x -= gap
            y += lh + lead
        self.full = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for p, x, y in self.words:
            self.full.alpha_composite(p, (x, y))

    def frame(self, t):
        if t <= 0:
            return None
        if t > 0.06 * len(self.words) + 0.6:
            return self.full
        pad = 60
        out = Image.new("RGBA", (self.w, self.h + pad), (0, 0, 0, 0))
        for i, (p, x, y) in enumerate(self.words):
            q = pr(t, i * 0.06, 0.5)
            if q <= 0:
                continue
            dy = (1 - out_back(q, 1.8)) * 46
            out.alpha_composite(with_alpha(p, clamp(q * 2.5)), (x, int(y + dy)))
        return out.crop((0, 0, self.w, self.h + pad))


# ------------------------------------------------------------------ brand parts
def g_pill(text, px=34, padx=36, pady=16):
    t = mp.text_img(text, "Black", px, WHITE)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    g = mp.brand_gradient(w, h)
    g.putalpha(mp.rounded(w, h, h // 2, (255, 255, 255, 255)).getchannel("A"))
    g.alpha_composite(t, (padx, pady))
    return soft_shadow(g, 14, 45, (0, 8))


def w_pill(text, px=34, fg=INK, padx=36, pady=16, weight="Bold", rtl=True):
    t = mp.text_img(text, weight, px, fg, rtl=rtl)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    p = mp.rounded(w, h, h // 2, WHITE + (255,))
    p.alpha_composite(t, (padx, pady))
    return soft_shadow(p, 14, 32, (0, 8))


def soft_shadow(im, blur=16, opacity=40, off=(0, 10)):
    s, pad = mp.shadow(im, blur=blur, opacity=opacity, offset=off)
    s.alpha_composite(im, (pad, pad))
    return s


def note_card(text, w_max):
    """White rounded card, gradient check dot on the right (RTL)."""
    t = mp.text_img(text, "Bold", 38, INK, rtl=is_fa(text))
    if t.width > w_max - 150:
        t = mp.fit(t, w_max - 150, t.height)
    h = max(92, t.height + 46)
    w = t.width + 150
    c = mp.rounded(w, h, 26, WHITE + (255,))
    d = 46
    dot = mp.brand_gradient(d, d)
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    dot.putalpha(m.resize((d, d), Image.LANCZOS))
    ck = Image.new("RGBA", (d * 4, d * 4), (0, 0, 0, 0))
    ImageDraw.Draw(ck).line([(d * 1.1, d * 2.1), (d * 1.75, d * 2.75), (d * 2.95, d * 1.35)],
                            fill=(255, 255, 255, 255), width=int(d * 0.42), joint="curve")
    dot.alpha_composite(ck.resize((d, d), Image.LANCZOS))
    c.alpha_composite(dot, (w - 30 - d, (h - d) // 2))
    c.alpha_composite(t, (w - 30 - d - 22 - t.width, (h - t.height) // 2))
    return soft_shadow(c, 18, 34, (0, 10))


def spotlight(w, h):
    s = Image.new("RGBA", (w + 300, h + 300), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((150, 150, w + 150, h + 150), fill=(255, 255, 255, 235))
    return blur_rgba(s, 80)


def background():
    bg = Image.new("RGBA", (W, H), BG + (255,))
    big = Image.new("RGBA", (int(W * 1.4), int(H * 1.4)), (0, 0, 0, 0))
    g = ImageDraw.Draw(big)
    g.ellipse((-200, -200, 900, 900), fill=PINK + (60,))
    g.ellipse((int(W * 1.4) - 1000, int(H * 1.4) - 1100, int(W * 1.4) + 150, int(H * 1.4) + 100),
              fill=BLUE + (60,))
    return bg, blur_rgba(big, 220)


# ------------------------------------------------------------------ 3D product model
_SESS = {}


def _midas():
    if "s" in _SESS:
        return _SESS["s"]
    sess = None
    try:
        import onnxruntime as ort
        f = CACHE / "midas_small.onnx"
        if not f.exists():
            CACHE.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(MIDAS_URL, str(f) + ".part")
            os.replace(str(f) + ".part", f)
        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 1
        sess = ort.InferenceSession(str(f), opt, providers=["CPUExecutionProvider"])
    except Exception as e:   # no network / no onnxruntime → geometric fallback
        print("depth model unavailable, using dome depth:", e, file=sys.stderr)
    _SESS["s"] = sess
    return sess


def depth_map(rgba):
    import cv2
    a = rgba[..., 3]
    inside = a > 0.5
    dt = cv2.distanceTransform(inside.astype(np.uint8), cv2.DIST_L2, 5)
    dome = np.sqrt(np.clip(dt / (dt.max() + 1e-6), 0, 1))         # rounded body
    sess = _midas()
    if sess is None:
        return dome * a
    rgb = cv2.resize(rgba[..., :3] * a[..., None] + (1 - a[..., None]), (256, 256),
                     interpolation=cv2.INTER_AREA)
    x = ((rgb - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None]
    d = sess.run(None, {sess.get_inputs()[0].name: x.astype(np.float32)})[0][0]
    d = cv2.resize(d, (rgba.shape[1], rgba.shape[0]), interpolation=cv2.INTER_CUBIC)
    v = d[inside]
    d = np.clip((d - np.percentile(v, 2)) / (np.ptp(v) + 1e-6), 0, 1)
    d = cv2.GaussianBlur(d, (0, 0), 2.0)
    return (0.6 * d + 0.4 * dome) * a


class Model3D:
    """Relief model of a product photo. render(yaw, pitch, light) → RGBA image."""

    def __init__(self, img, box_w, box_h, relief=0.16, thick=0.07):
        import cv2
        im = img.convert("RGBA")
        if np.asarray(im.getchannel("A")).min() > 250:      # opaque photo → cut the white away
            im = mp.remove_white_bg(im.convert("RGB"))
        im = mp.trim(im)
        im = mp.fit(im, box_w, box_h)
        rgba = np.asarray(im).astype(np.float32) / 255
        # pull the cut-out edge in by ~2px so no white halo from the photo background remains
        a0 = (rgba[..., 3] > 0.5).astype(np.uint8)
        a0 = cv2.erode(a0, np.ones((3, 3), np.uint8))
        rgba[..., 3] = cv2.GaussianBlur(a0.astype(np.float32), (0, 0), 0.8) * (rgba[..., 3] > 0.02)
        h, w = rgba.shape[:2]
        dep = depth_map(rgba)
        al = rgba[..., 3]
        ys, xs = np.nonzero(al > 0.02)
        size = max(w, h)
        z = dep[ys, xs] * relief * size
        # normals from the depth (for lighting)
        gy, gx = np.gradient(dep * relief * size)
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        col = rgba[ys, xs, :3]
        pts = [np.stack([xs - w / 2, ys - h / 2, z], -1)]
        cols = [col]
        nrm = [n[ys, xs]]
        alp = [al[ys, xs]]
        # side wall: the silhouette edge extruded backwards
        er = cv2.erode((al > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8))
        edge = ((al > 0.5) & (er == 0))
        ey, ex = np.nonzero(edge)
        mean = rgba[al > 0.5, :3].mean(0) if (al > 0.5).any() else np.array([0.3, 0.3, 0.3])
        base = np.repeat(mean[None], len(ey), 0)
        T = thick * size
        steps = max(4, int(T / 1.2))
        cx_, cy_ = w / 2, h / 2
        ang = np.arctan2(ey - cy_, ex - cx_)
        side_n = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], -1)
        for k in range(1, steps + 1):
            zz = dep[ey, ex] * relief * size * 0.3 - T * k / steps
            pts.append(np.stack([ex - w / 2, ey - h / 2, zz], -1))
            cols.append(base * 0.42 + 0.04)
            nrm.append(side_n)
            alp.append(np.ones(len(ey)))
        self.P = np.concatenate(pts).astype(np.float32)
        self.C = np.concatenate(cols).astype(np.float32)
        self.N = np.concatenate(nrm).astype(np.float32)
        self.A = np.concatenate(alp).astype(np.float32)
        self.w, self.h = w, h
        self.f = size * 3.2
        self.cache = {}

    def render(self, yaw, pitch=0.0, light=0.0, scale=1.0):
        key = (round(yaw, 1), round(pitch, 1), round(light, 2), round(scale, 3))
        if key in self.cache:
            return self.cache[key]
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
        Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)
        R = Rx @ Ry
        P = self.P @ R.T
        N = self.N @ R.T
        s = self.f / (self.f - P[:, 2])
        k = SS_3D = 1                                   # noqa: F841
        u = P[:, 0] * s * scale
        v = P[:, 1] * s * scale
        mw = int(max(self.w, self.h) * 1.25 * scale) + 8
        mh = int(self.h * 1.25 * scale + abs(sy) * 40) + 8
        ox, oy = mw / 2, mh / 2
        ui = np.clip((u + ox).astype(np.int32), 0, mw - 2)
        vi = np.clip((v + oy).astype(np.int32), 0, mh - 2)
        # lighting: key light sweeps with `light`, plus a specular glint
        lx = math.sin(light) * 0.75
        L = np.array([lx, -0.45, 0.62], np.float32)
        L /= np.linalg.norm(L)
        lam = np.clip(N @ L, 0, 1)
        Hh = L + np.array([0, 0, 1], np.float32)
        Hh /= np.linalg.norm(Hh)
        spec = np.clip(N @ Hh, 0, 1) ** 40
        shade = 0.80 + 0.30 * lam
        C = np.clip(self.C * shade[:, None] + spec[:, None] * 0.35, 0, 1)
        order = np.argsort(P[:, 2], kind="stable")      # far first, near last wins
        img = np.zeros((mh, mw, 4), np.float32)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            o = order
            img[vi[o] + dy, ui[o] + dx, :3] = C[o]
            img[vi[o] + dy, ui[o] + dx, 3] = np.maximum(img[vi[o] + dy, ui[o] + dx, 3], self.A[o])
        out = Image.fromarray((img * 255).astype(np.uint8), "RGBA")
        r, g, b, a = out.split()
        out = Image.merge("RGBA", (r, g, b, a.filter(ImageFilter.GaussianBlur(0.9))))
        if len(self.cache) < 400:
            self.cache[key] = out
        return out


class Product3D:
    """A 3D product on a spotlight with reflection + contact shadow, spring-in then sway."""

    def __init__(self, img, box_w, box_h, seed=1, side=1):
        self.m = Model3D(img, box_w, box_h)
        self.spot = spotlight(int(box_w * 1.15), int(box_h * 0.95))
        self.phase = random.Random(seed).uniform(0, 6.28)
        self.side = side

    def frame(self, t, scale=1.0):
        if t <= 0:
            return None, 0
        p = spring(t * 1.15)
        yaw = (1 - p) * 70 * self.side + math.sin(t * 1.1 + self.phase) * 13 * clamp(t - 0.6)
        pitch = 8 + (1 - p) * 10 + math.sin(t * 0.8 + self.phase) * 3
        light = t * 0.9 + self.phase
        sc = scale * (0.82 + 0.18 * out_expo(pr(t, 0, 0.7)))
        im = self.m.render(yaw, pitch, light, sc)
        a = clamp(t / 0.25)
        bb = im.getchannel("A").getbbox() or (0, 0, im.width, im.height)
        bottom = bb[3]
        pad = 40
        out = Image.new("RGBA", (max(im.width, self.spot.width) + 2 * pad,
                                 int(im.height * 1.45) + 2 * pad), (0, 0, 0, 0))
        cx = out.width // 2
        oy = pad + int((im.height - bottom) * 0.0)
        # spotlight behind
        out.alpha_composite(with_alpha(self.spot, a), (cx - self.spot.width // 2, oy + im.height // 2 - self.spot.height // 2))
        # contact shadow
        sw = int((bb[2] - bb[0]) * 0.9)
        sh_ = Image.new("RGBA", (sw + 120, 160), (0, 0, 0, 0))
        ImageDraw.Draw(sh_).ellipse((60, 55, sw + 60, 105), fill=(30, 30, 60, int(90 * a)))
        sh_ = blur_rgba(sh_, 18)
        out.alpha_composite(sh_, (cx - sh_.width // 2, oy + bottom - 80))
        # reflection
        refl = im.crop((0, bb[1], im.width, bottom)).transpose(Image.FLIP_TOP_BOTTOM)
        rh = int(refl.height * 0.3)
        refl = refl.crop((0, 0, refl.width, rh))
        grad = Image.linear_gradient("L").resize((refl.width, rh)).point(lambda v: int((255 - v) * 0.22 * a))
        ra = Image.fromarray(np.minimum(np.asarray(refl.getchannel("A")), np.asarray(grad)))
        refl.putalpha(ra)
        out.alpha_composite(refl, (cx - im.width // 2, oy + bottom + 6))
        out.alpha_composite(with_alpha(im, a), (cx - im.width // 2, oy))
        return out, oy + bottom


# ------------------------------------------------------------------ stage
class El:
    """Generic element: src(lt) -> Image|None, placed at (x, y) centre, entrance + parallax."""

    def __init__(self, src, x, y, t_in=0.0, enter="rise", depth=1.0, dur=0.6, anchor="c"):
        self.src, self.x, self.y, self.t_in = src, x, y, t_in
        self.enter, self.depth, self.dur, self.anchor = enter, depth, dur, anchor

    def draw(self, c, t, cam):
        lt = t - self.t_in
        if lt <= 0 and self.enter != "none":
            return
        im = self.src(lt) if callable(self.src) else self.src
        if im is None:
            return
        x, y, a, s = self.x, self.y, 1.0, 1.0
        if self.enter != "none":
            p = out_expo(pr(lt, 0, self.dur))
            a = clamp(lt / (self.dur * 0.4))
            if self.enter == "rise":
                y += (1 - p) * 80
            elif self.enter == "slide_r":
                x += (1 - p) * 260
            elif self.enter == "pop":
                s = 0.7 + 0.3 * out_back(pr(lt, 0, self.dur), 2.0)
        z, px_, py_ = cam
        zz = 1 + (z - 1) * self.depth
        x = W / 2 + (x - W / 2) * zz + px_ * self.depth
        y = H / 2 + (y - H / 2) * zz + py_ * self.depth
        s *= zz
        if abs(s - 1) > 0.003:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
        im = with_alpha(im, a)
        if self.anchor == "r":          # x = right edge
            c.alpha_composite(im, (int(x - im.width), int(y - im.height / 2)))
        else:
            c.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))


class Scene:
    def __init__(self, start, dur, els, pan=(1, 1), lead=0.0):
        self.start, self.dur, self.els, self.pan, self.lead = start, dur, els, pan, lead

    def cam(self, lt):
        q = in_out_cubic(pr(lt, 0, self.dur + WIPE))
        return 1 + 0.04 * q, self.pan[0] * 18 * q, self.pan[1] * -12 * q

    def draw(self, c, t):
        lt = t - self.start + self.lead
        cam = self.cam(lt)
        for e in self.els:
            e.draw(c, lt, cam)


def kt(text, px, color=INK, weight="Black", max_w=None, lines=2):
    k = KText(text, px, color, weight, max_w, lines)
    return k.frame


def product_el(path, x, y, box_w, box_h, t_in, seed, side=1, depth=1.2):
    pm = Product3D(Image.open(path), box_w, box_h, seed=seed, side=side)

    def src(lt):
        im, _ = pm.frame(lt)
        return im
    return El(src, x, y + box_h * 0.3, t_in, enter="none", depth=depth)


def caption_img(text):
    """Product caption under the model: brand in gradient, model in ink (like the story)."""
    parts = text.split()
    if len(parts) >= 2 and is_fa(parts[0]):
        b = mp.gradient_text(parts[0], "Black", 40, rtl=True)
        m = mp.text_img(" ".join(parts[1:]), "Black", 56, INK, rtl=is_fa(" ".join(parts[1:])))
        out = Image.new("RGBA", (max(b.width, m.width), b.height + m.height + 12), (0, 0, 0, 0))
        out.alpha_composite(b, ((out.width - b.width) // 2, 0))
        out.alpha_composite(m, ((out.width - m.width) // 2, b.height + 12))
        return out
    return mp.text_img(text, "Black", 56, INK, rtl=is_fa(text))


# ------------------------------------------------------------------ template
def build(spec, base: Path):
    global W, H
    W, H = (1080, 1920) if spec.get("format", "reel") == "reel" else (1080, 1350)
    cl.W, cl.H = W, H
    reel = H == 1920
    sd = random.Random(spec.get("seed", 7))
    rs = lambda: sd.randint(1, 10_000)  # noqa: E731
    top = 150 if reel else 70
    logo = mp.brand_lockup(58 if reel else 50)
    logo_el = lambda: El(logo, W / 2, top, 0, enter="none", depth=0.5)  # noqa: E731
    pans = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    scenes, t0 = [], 0.0
    nsteps = len(spec["steps"])

    # ---- hook (readable from frame 0)
    hk = spec["hook"]
    els = [logo_el()]
    y = top + (150 if reel else 110)
    if hk.get("sub"):
        els.append(El(g_pill(hk["sub"], 34 if reel else 30), W / 2, y, 0, enter="none", depth=0.7))
        y += 115 if reel else 95
    else:
        y += 20
    l1 = KText(hk["l1"], 104 if reel else 88, max_w=W - 90, lines=1)
    els.append(El(lambda lt, k=l1: k.full, W / 2, y + l1.h / 2, 0, enter="none", depth=0.8))
    y += l1.h + 28
    l2 = KText(hk["l2"], 92 if reel else 76, "grad", max_w=W - 90, lines=1)
    els.append(El(l2.frame, W / 2, y + (l2.h + 60) / 2, 0.15, enter="none", depth=0.8))
    y += l2.h + 40
    ims = hk.get("images", [])[:3]
    n = len(ims)
    if n:
        area_top, area_bot = y + 40, H - (300 if reel else 110)
        cyp = (area_top + area_bot) / 2
        if n == 1:
            spots = [(W / 2, cyp, 820, 640 if reel else 470)]
        elif n == 2:
            spots = ([(W / 2, cyp - 300, 860, 430), (W / 2, cyp + 300, 860, 430)] if reel
                     else [(W * 0.73, cyp, 470, 420), (W * 0.27, cyp, 470, 420)])
        else:
            spots = ([(W / 2, cyp - 330, 640, 330), (W * 0.29, cyp + 230, 440, 330), (W * 0.71, cyp + 230, 440, 330)]
                     if reel else [(W * 0.78, cyp, 320, 330), (W * 0.5, cyp, 320, 330), (W * 0.22, cyp, 320, 330)])
        for i, (p, (sx, sy, bw, bh)) in enumerate(zip(ims, spots)):
            els.append(product_el(base / p, sx, sy, bw, bh, 0.25 + i * 0.22, rs(), side=1 if i % 2 == 0 else -1))
    scenes.append(Scene(t0, 3.4, els, pans[0]))
    t0 += 3.4

    # ---- steps
    for k, st in enumerate(spec["steps"]):
        els = [logo_el()]
        y = top + (140 if reel else 100)
        els.append(El(g_pill(f"نکته {k + 1} از {nsteps}" if nsteps > 1 else "نکته", 30), W / 2, y, 0.05,
                      enter="pop", dur=0.45, depth=0.7))
        y += 100 if reel else 80
        tt = KText(st["title"], 76 if reel else 62, INK, max_w=W - 140)
        els.append(El(tt.frame, W / 2, y + (tt.h + 60) / 2, 0.15, enter="none", depth=0.8))
        y += tt.h + 20
        notes = st.get("notes", [])[:3]
        cards = [note_card(nt, W - 120) for nt in notes]
        notes_h = sum(c.height - 108 for c in cards) + (len(cards) - 1) * 20
        bottom_safe = H - (330 if reel else 70)
        area_top, area_bot = y + 20, bottom_safe - notes_h - 20
        prods = st.get("products", [])[:2]
        cyp = (area_top + area_bot) / 2
        cap_h = 150
        avail = area_bot - area_top
        if len(prods) == 1:
            bh = min(560, avail - cap_h - 120)
            spots = [(W / 2, area_top + 30 + bh / 2, 860, bh)]
        elif len(prods) == 2 and reel and avail > 820:
            bh = min(360, (avail - 2 * cap_h - 120) / 2)
            y1 = area_top + 20 + bh / 2
            y2 = y1 + bh + cap_h + 70
            spots = [(W / 2, y1, 820, bh), (W / 2, y2, 820, bh)]
        elif prods:
            bh = max(220, min(420, avail - cap_h - 120))
            spots = [(W * 0.73, area_top + 30 + bh / 2, 470, bh), (W * 0.27, area_top + 30 + bh / 2, 470, bh)]
        else:
            spots = []
        for i, (pd, (sx, sy, bw_, bh_)) in enumerate(zip(prods, spots)):
            els.append(product_el(base / pd["img"], sx, sy, bw_, bh_, 0.3 + i * 0.25, rs(),
                                  side=1 if (i + k) % 2 == 0 else -1))
            if pd.get("caption"):
                els.append(El(caption_img(pd["caption"]), sx, sy + bh_ * 0.5 + 115, 0.75 + i * 0.25,
                              enter="rise", depth=1.1))
        if st.get("tag") and spots:
            sx, sy, bw_, bh_ = spots[0]
            tg = g_pill(st["tag"], 32)
            els.append(El(tg, W - 50 - tg.width / 2, sy - bh_ * 0.5 + 10,
                          0.9, enter="pop", dur=0.45, depth=1.25))
        t_note = 1.0
        yy = bottom_safe - notes_h
        for i, cimg in enumerate(cards):
            els.append(El(cimg, W - 6, yy + (cimg.height - 108) / 2, t_note + i * 0.42, enter="slide_r",
                          dur=0.55, depth=1.05, anchor="r"))
            yy += cimg.height - 108 + 20
        dur = max(3.4, t_note + 0.42 * len(notes) + 1.7)
        scenes.append(Scene(t0, dur, els, pans[(k + 1) % 4], lead=0.3))
        t0 += dur

    # ---- outro
    oc = spec["outro"]
    els = []
    cy = H * (0.30 if reel else 0.20)
    big = mp.brand_lockup(110 if reel else 90)
    els.append(El(big, W / 2, cy, 0.0, enter="pop", dur=0.5, depth=0.7))
    o1 = KText(oc["l1"], 80 if reel else 66, max_w=W - 90, lines=1)
    els.append(El(o1.frame, W / 2, cy + 190 + o1.h / 2, 0.2, enter="none", depth=0.85))
    yy = cy + 190 + o1.h + 40
    o2 = KText(oc["l2"], 54 if reel else 46, "grad", weight="Black")
    els.append(El(o2.frame, W / 2, yy + o2.h / 2 + 20, 0.45, enter="none", depth=0.85))
    yy += o2.h + 140
    phone = g_pill(PHONE, 58, padx=50, pady=22)
    els.append(El(lambda lt, p=phone: p if lt < 1.4 else p.resize(
        (int(p.width * (1 + 0.035 * math.sin((lt - 1.4) * 5))), int(p.height * (1 + 0.035 * math.sin((lt - 1.4) * 5)))),
        Image.BICUBIC), W / 2, yy, 0.75, enter="pop", dur=0.5))
    yy += 140
    els.append(El(w_pill(SITE, 44, rtl=False, weight="Black"), W / 2, yy, 0.95, enter="rise"))
    yy += 120
    if oc.get("warranty"):
        els.append(El(w_pill(oc["warranty"], 38), W / 2, yy, 1.15, enter="rise"))
    scenes.append(Scene(t0, 3.8, els, pans[(nsteps + 1) % 4], lead=0.3))
    t0 += 3.8
    return scenes, t0


# ------------------------------------------------------------------ render
STATE = {}


def make_static():
    bg, glow = background()
    rng = np.random.default_rng(5)
    grains = [rng.normal(0, 3.0, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]
    grains = [np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR))[..., None] for g in grains]
    sheets = []
    stamp = mp.brand_lockup(120)
    for i, kind in enumerate(["white", "grad", "pink", "blue"]):
        sw, shh = int(W * 1.7), int(H * 1.5)
        if kind == "grad":
            sh = mp.brand_gradient(sw, shh)
            st = mp.brand_lockup(120)
            st = Image.merge("RGBA", (*[Image.new("L", st.size, 255)] * 3, st.getchannel("A")))
        else:
            col = {"white": WHITE, "pink": SOFT_PINK, "blue": SOFT_BLUE}[kind]
            sh = paper_texture(sw, shh, col, seed=200 + i, grain=4)
            st = stamp
        sh.putalpha(torn_mask(sw, shh, 300 + i, rough=28, step=22))
        sh.alpha_composite(st, ((sw - st.width) // 2, (shh - st.height) // 2))
        pad = 60
        full = Image.new("RGBA", (sw + 2 * pad, shh + 2 * pad), (0, 0, 0, 0))
        dark = Image.new("RGBA", sh.size, (40, 40, 80, 255))
        dark.putalpha(sh.getchannel("A").point(lambda v: v * 70 // 255))
        full.alpha_composite(dark, (pad + 14, pad + 20))
        full = cl.blur(full, 18)
        full.alpha_composite(sh, (pad, pad))
        sheets.append(full.rotate(-9 if i % 2 == 0 else 9, expand=True, resample=Image.BICUBIC))
    return bg, glow, grains, sheets


def frame_at(T):
    scenes, total = STATE["scenes"], STATE["total"]
    bg, glow, grains, sheets = STATE["static"]
    c = bg.copy()
    q = T / max(total, 1)
    ox = int((glow.width - W) / 2 + math.sin(q * math.pi * 2) * 120)
    oy = int((glow.height - H) / 2 + math.cos(q * math.pi * 1.4) * 140)
    c.alpha_composite(glow.crop((ox, oy, ox + W, oy + H)))
    idx = 0
    for i, s in enumerate(scenes):
        if T >= s.start:
            idx = i
    scenes[idx].draw(c, T)
    for i, s in enumerate(scenes[1:], start=1):
        b = s.start
        if b - WIPE <= T <= b + WIPE:
            p = in_out_cubic(pr(T, b - WIPE, 2 * WIPE))
            sh = sheets[(i - 1) % len(sheets)]
            d = 1 if i % 2 else -1
            cx = W / 2 + d * (1 - 2 * p) * (sh.width * 0.5 + W * 0.55)
            cy = H / 2 + (1 - 2 * p) * 120
            c.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)))
    arr = np.asarray(c.convert("RGB"), dtype=np.float32)
    return np.clip(arr + grains[int(T * FPS) // 2 % 4], 0, 255).astype(np.uint8)


def _init(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    STATE["scenes"], STATE["total"] = build(spec, Path(spec_path).parent)
    STATE["static"] = make_static()


def _job(k):
    return frame_at(k / FPS).tobytes()


def main():
    spec_path, out = Path(sys.argv[1]), sys.argv[2]
    _midas()          # download the depth model once, before the worker pool starts
    _init(spec_path)
    total = STATE["total"]
    if "--preview" in sys.argv:
        d = Path(sys.argv[sys.argv.index("--preview") + 1])
        d.mkdir(parents=True, exist_ok=True)
        times = [0.0, 0.6, 1.8]
        for s in STATE["scenes"][1:]:
            times += [s.start - 0.1, s.start + 0.7, s.start + s.dur - 0.4]
        for T in times:
            Image.fromarray(frame_at(T)).save(d / f"k_{T:05.2f}.jpg", quality=86)
        print(f"preview {len(times)} frames, {total:.1f}s")
        return
    n = int(total * FPS)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    mu = spec.get("music", {})
    if mu.get("mood") == "none":
        audio_in = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        afilter = []
    else:
        import music
        cuts = [s.start for s in STATE["scenes"][1:]]
        st, info = music.make(total, cuts, mu.get("mood"), int(spec.get("seed", 7)))
        wav = str(out).replace(".mp4", "-music.wav")
        music.write_wav(wav, st)
        print("music", info)
        audio_in = ["-i", wav]
        afilter = ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           *audio_in, "-shortest", *afilter,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = max(1, min(4, os.cpu_count() or 1))
    with Pool(workers, initializer=_init, initargs=(str(spec_path),)) as pool:
        for buf in pool.imap(_job, range(n), chunksize=8):
            proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    Image.fromarray(frame_at(2.2)).save(str(out).replace(".mp4", "-cover.jpg"), quality=92)
    print(f"{'reel' if H == 1920 else 'post'} {W}x{H} {total:.1f}s")


if __name__ == "__main__":
    main()
