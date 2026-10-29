"""lalehstore cinematic paper-collage renderer (smooth 30 fps motion + kinetic typography).

Same JSON spec as collage.py (hook / steps / outro), plus an optional "music" block that is
only used when scheduling (Instagram audio), never rendered into the file:

{
  "format": "reel" | "post",
  "seed": 30,
  "music": {"query": "song title or artist", "audioVolume": 70},
  "hook":  {"l1": "...", "l2": "...", "sub": "...", "images": ["a.webp"]},
  "steps": [{"title": "...", "products": [{"img": "a.webp", "caption": "..."}],
             "notes": ["...", "..."], "tag": "..."}],
  "outro": {"l1": "...", "l2": "...", "warranty": "..."}
}

Look: kraft-paper table, torn paper labels, polaroids and tape (collage.py parts), but
animated smoothly: eased entrances, a slow camera push with parallax, word-by-word kinetic
type (right to left), notes that slide in one by one, a marker arrow that draws itself and
a full-screen torn-paper wipe between scenes. Film grain + vignette on top.

Usage:
  python3 -I cinema.py spec.json out.mp4 [--preview DIR]
"""
import json
import math
import random
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collage as cl  # noqa: E402
import make_post as mp  # noqa: E402
from collage import (BLUE, CREAM, INK, KRAFT, LALEZAR, PHONE, PINK, SITE, SKY, SS,  # noqa: E402
                     WHITE, YELLOW, load_img, logo_stamp, marker_arrow, paper_texture,
                     polaroid, tape, torn_mask)

FPS = 30
W, H = 1080, 1920
WIPE = 0.36          # half length of the paper wipe between scenes (s)


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


def out_back(x, s=1.5):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def is_fa(s):
    return any("؀" <= ch <= "ۿ" for ch in s)


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


# ------------------------------------------------------------------ kinetic type
def word_img(word, px, fg, font="lalezar", weight="Black"):
    """One word (or one LTR run) on a fixed-height canvas, so every word shares a baseline."""
    if font == "lalezar" and cl._is_persian_only(word):
        f = ImageFont.truetype(LALEZAR, px * SS, layout_engine=ImageFont.Layout.RAQM)
    else:
        f = mp.font(weight, px * SS)
    hh = int(px * 2.6 * SS)
    ww = int(len(word) * px * SS * 1.3 + 4 * px * SS)
    layer = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((ww // 2, int(px * 1.75 * SS)), word, font=f, fill=tuple(fg) + (255,),
                               anchor="ms", direction="rtl" if is_fa(word) else "ltr")
    bb = layer.getchannel("A").getbbox()
    layer = layer.crop((bb[0], 0, bb[2], hh))
    return layer.resize((max(1, layer.width // SS), hh // SS), Image.LANCZOS)


def chunks(text):
    """Persian words one by one; consecutive Latin/number tokens stay together (LTR run)."""
    out = []
    for tok in text.split():
        if out and not is_fa(tok) and not is_fa(out[-1]):
            out[-1] += " " + tok
        else:
            out.append(tok)
    return out


class KLabel:
    """Torn paper strip that unrolls from the right, then its words pop up one by one."""

    def __init__(self, text, px, bg, fg=INK, seed=3, font="lalezar", weight="Black",
                 padx=44, pady=22, max_w=None, rough=10):
        max_w = max_w or W - 90
        parts = chunks(text)
        while True:
            imgs = [word_img(p, px, fg, font, weight) for p in parts]
            gap = int(px * 0.30)
            tw = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
            if tw + 2 * padx <= max_w or px <= 22:
                break
            px = int(px * 0.92)
        top = min(i.getchannel("A").getbbox()[1] for i in imgs)
        bot = max(i.getchannel("A").getbbox()[3] for i in imgs)
        imgs = [i.crop((0, top, i.width, bot)) for i in imgs]
        th = bot - top
        self.w, self.h = tw + 2 * padx, th + 2 * pady
        paper = paper_texture(self.w, self.h, bg, seed=seed, grain=6)
        paper.putalpha(torn_mask(self.w, self.h, seed, rough=rough))
        self.paper = paper
        self.pad = 26
        sh = Image.new("RGBA", (self.w + 2 * self.pad, self.h + 2 * self.pad), (0, 0, 0, 0))
        dark = Image.new("RGBA", paper.size, (40, 30, 20, 255))
        dark.putalpha(paper.getchannel("A").point(lambda v: v * 85 // 255))
        sh.alpha_composite(dark, (self.pad + 6, self.pad + 9))
        self.shadow = cl.blur(sh, 8)
        rtl = is_fa(text)
        self.words, x = [], (padx + tw if rtl else padx)
        for im in imgs:
            if rtl:
                x -= im.width
                self.words.append((im, x, pady))
                x -= gap
            else:
                self.words.append((im, x, pady))
                x += im.width + gap
        self.order = list(range(len(self.words)))   # reading order (already RTL)
        self.cache = {}

    def frame(self, t, instant=False):
        """Image of the label at local time t (t=0 → starts appearing)."""
        if instant:
            t = 10.0
        if t <= 0:
            return None
        ps = out_expo(pr(t, 0, 0.5))
        key = None
        if t > 0.5 + 0.07 * len(self.words) + 0.5:
            key = "done"
            if key in self.cache:
                return self.cache[key]
        cw = max(1, int(self.w * ps))
        P = self.pad
        out = Image.new("RGBA", (self.w + 2 * P, self.h + 2 * P), (0, 0, 0, 0))
        x0 = self.w - cw                       # unroll from the right edge
        out.alpha_composite(self.shadow.crop((x0 + P, 0, self.w + 2 * P, self.h + 2 * P)), (x0 + P, 0))
        out.alpha_composite(self.paper.crop((x0, 0, self.w, self.h)), (x0 + P, P))
        for i, (im, x, y) in enumerate(self.words):
            q = pr(t, 0.16 + i * 0.075, 0.42)
            if q <= 0:
                continue
            dy = (1 - out_back(q, 1.7)) * self.h * 0.42
            out.alpha_composite(with_alpha(im, clamp(q * 2.2)), (int(x + P), int(y + P + dy)))
        if key:
            self.cache[key] = out
        return out


def draw_on(img):
    """Callable that reveals an image left→right (a marker stroke being drawn)."""
    def f(t):
        q = in_out_cubic(pr(t, 0, 0.55))
        if q <= 0:
            return None
        cw = max(1, int(img.width * q))
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.alpha_composite(img.crop((0, 0, cw, img.height)), (0, 0))
        return out
    return f


# ------------------------------------------------------------------ stage
class El:
    """An animated element. src = Image or callable(local_t) -> Image|None."""

    def __init__(self, src, x, y, rot=0.0, t_in=0.0, enter="drop", depth=1.0,
                 dur=0.7, float_amp=0.0, seed=1, instant=False, own_time=False):
        self.src, self.x, self.y, self.rot, self.t_in = src, x, y, rot, t_in
        self.enter, self.depth, self.dur, self.float_amp = enter, depth, dur, float_amp
        self.phase = random.Random(seed).uniform(0, 6.28)
        self.instant, self.own_time = instant, own_time
        self.cache = {}

    def draw(self, c, t, cam):
        lt = t - self.t_in
        if lt < 0 and not self.instant:
            return
        if callable(self.src):
            im = self.src(lt if not self.instant else 10.0)
            if im is None:
                return
        else:
            im = self.src
        p = 1.0 if (self.instant or self.own_time) else out_expo(pr(lt, 0, self.dur))
        x, y, rot, s, a = self.x, self.y, self.rot, 1.0, 1.0
        if not (self.instant or self.own_time):
            a = clamp(pr(lt, 0, self.dur * 0.35))
            if self.enter == "drop":
                s = 1.22 - 0.22 * p
                rot += (1 - p) * 9
                y -= (1 - p) * 40
            elif self.enter == "rise":
                y += (1 - p) * 170
            elif self.enter == "slide_r":
                x += (1 - p) * W * 0.75
                rot += (1 - p) * 12
            elif self.enter == "slide_l":
                x -= (1 - p) * W * 0.75
                rot -= (1 - p) * 12
            elif self.enter == "pop":
                s = 0.6 + 0.4 * out_back(pr(lt, 0, self.dur), 2.2)
        if self.float_amp:
            ph = t * 2 * math.pi / 4.0 + self.phase
            y += math.sin(ph) * self.float_amp
            rot += math.sin(ph * 0.8) * 0.5
        # camera (zoom around centre + pan), stronger on near layers
        z, px_, py_ = cam
        zz = 1 + (z - 1) * self.depth
        x = W / 2 + (x - W / 2) * zz + px_ * self.depth
        y = H / 2 + (y - H / 2) * zz + py_ * self.depth
        s *= zz
        rq, sq = round(rot, 1), round(s, 3)
        if callable(self.src):
            out = im
            if abs(rq) > 0.05:
                out = out.rotate(rq, expand=True, resample=Image.BICUBIC)
            if abs(sq - 1) > 0.002:
                out = out.resize((max(1, int(out.width * sq)), max(1, int(out.height * sq))), Image.BICUBIC)
        else:
            key = (rq, sq)
            out = self.cache.get(key)
            if out is None:
                out = im.rotate(rq, expand=True, resample=Image.BICUBIC) if abs(rq) > 0.05 else im
                if abs(sq - 1) > 0.002:
                    out = out.resize((max(1, int(out.width * sq)), max(1, int(out.height * sq))), Image.BICUBIC)
                if len(self.cache) < 60:
                    self.cache[key] = out
        out = with_alpha(out, a)
        c.alpha_composite(out, (int(x - out.width / 2), int(y - out.height / 2)))


class Scene:
    def __init__(self, start, dur, els, pan=(1, 1), lead=0.0):
        # lead: how far the scene's own clock is ahead, so it is already moving when the wipe uncovers it
        self.start, self.dur, self.els, self.pan, self.lead = start, dur, els, pan, lead

    def cam(self, lt):
        q = in_out_cubic(pr(lt, 0, self.dur + WIPE))
        return 1 + 0.045 * q, self.pan[0] * 22 * q, self.pan[1] * -14 * q

    def draw(self, c, t):
        lt = t - self.start + self.lead
        cam = self.cam(lt)
        for e in self.els:
            e.draw(c, lt, cam)


# ------------------------------------------------------------------ template
def build(spec, base_dir: Path):
    global W, H
    W, H = (1080, 1920) if spec.get("format", "reel") == "reel" else (1080, 1350)
    cl.W, cl.H = W, H
    reel = H == 1920
    top = 250 if reel else 110
    sd = random.Random(spec.get("seed", 7))
    rs = lambda: sd.randint(1, 10_000)  # noqa: E731
    rot = lambda m=3.0: sd.uniform(-m, m)  # noqa: E731
    img = lambda p: load_img(base_dir / p)  # noqa: E731
    stamp = logo_stamp()
    scenes, t0 = [], 0.0
    pans = [(1, 1), (-1, 1), (1, -1), (-1, -1)]

    def label(text, px, bg, fg=INK, font="lalezar", **kw):
        return KLabel(text, px, bg, fg=fg, seed=rs(), font=font, **kw)

    def lab_el(lb, x, y, t_in, r=None, instant=False, depth=1.0):
        return El(lambda lt, lb=lb, inst=instant: lb.frame(lt, instant=inst), x, y,
                  rot(2) if r is None else r, t_in, depth=depth, seed=rs(), instant=instant, own_time=True)

    # ---- hook: title readable from the very first frame
    hk = spec["hook"]
    els = [El(stamp, 230, top, -3, 0, depth=0.6, instant=True, seed=rs())]
    ims = hk.get("images", [])[:4]
    n = len(ims)
    if n:
        pw = 330 if n >= 3 else (420 if n == 2 else (520 if reel else 440))
        ys = (top + 1010) if reel else (top + 830)
        xs = {1: [W / 2], 2: [320, 760], 3: [215, 540, 865], 4: [300, 780, 300, 780]}[n]
        for i, p in enumerate(ims):
            y = ys if n < 4 else (ys - 180 + (i // 2) * 420 if reel else ys - 120 + (i // 2) * 330)
            pw_i = pw if n < 4 else (380 if reel else 300)
            y += sd.uniform(-25, 25)
            els.append(El(polaroid(img(p), pw_i, seed=rs()), xs[i], y, rot(7), 0.35 + i * 0.16,
                          enter="drop", depth=1.25, float_amp=6, seed=rs()))
            els.append(El(tape(170, 52, seed=rs(), angle=rot(14)), xs[i], y - pw_i * 0.58, 0,
                          0.6 + i * 0.16, enter="pop", dur=0.4, depth=1.25, seed=rs()))
    l1 = label(hk["l1"], 132, YELLOW)
    l2 = label(hk["l2"], 112, PINK, fg=WHITE)
    els.append(lab_el(l1, W / 2, top + 230, 0, instant=True, depth=0.9))
    els.append(lab_el(l2, W / 2, top + 420, 0.2, depth=0.9))
    if hk.get("sub"):
        els.append(lab_el(label(hk["sub"], 46, CREAM, font="vazir"), W / 2, top + 575, 0.55))
    if n:
        arr = marker_arrow(230, 150, BLUE, seed=rs())
        els.append(El(draw_on(arr), W - 210, top + (640 if hk.get("sub") else 570), 0, 1.1,
                      own_time=True, depth=1.1, seed=rs()))
    scenes.append(Scene(t0, 3.4, els, pans[0]))
    t0 += 3.4

    # ---- steps
    for k, st in enumerate(spec["steps"]):
        els = [El(stamp, 230, top, -3, 0, depth=0.6, instant=True, seed=rs())]
        els.append(lab_el(label(st["title"], 70, CREAM if k % 2 == 0 else SKY, font="vazir"),
                          W / 2, top + 170, 0.12))
        prods = st.get("products", [])[:2]
        mid = (top + 720) if reel else (top + 540)
        if len(prods) == 1:
            pw = 600 if reel else 470
            els.append(El(polaroid(img(prods[0]["img"]), pw, seed=rs(), caption=prods[0].get("caption")),
                          W / 2, mid, rot(4), 0.3, enter="slide_r" if k % 2 == 0 else "slide_l",
                          dur=0.9, depth=1.25, float_amp=7, seed=rs()))
            els.append(El(tape(210, 60, seed=rs(), angle=rot(8)), W / 2, mid - pw * 0.6, 0, 0.85,
                          enter="pop", dur=0.4, depth=1.25, seed=rs()))
        elif len(prods) == 2:
            pw = 470 if reel else 400
            for i, (pd, x) in enumerate(zip(prods, (W * 0.70, W * 0.30))):   # RTL: first on the right
                y = mid + (0 if i == 0 else 50)
                els.append(El(polaroid(img(pd["img"]), pw, seed=rs(), caption=pd.get("caption")),
                              x, y, rot(6), 0.3 + i * 0.22, enter="slide_r" if i == 0 else "slide_l",
                              dur=0.9, depth=1.25, float_amp=6, seed=rs()))
                els.append(El(tape(190, 56, seed=rs(), angle=rot(12)), x, y - pw * 0.6, 0, 0.85 + i * 0.22,
                              enter="pop", dur=0.4, depth=1.25, seed=rs()))
        notes = st.get("notes", [])[:3]
        t_note = 0.9
        if notes:
            gap = 112 if reel else 92
            y0 = (H - 560 - (len(notes) - 1) * gap / 2) if reel else (H - 250 - (len(notes) - 1) * gap / 2)
            for i, nt in enumerate(notes):
                lb = label(nt, 40, WHITE if (i + k) % 2 == 0 else CREAM, font="vazir", weight="Bold",
                           padx=30, pady=16, max_w=W - 140, rough=6)
                x = W - 70 - lb.w / 2 - 10        # right aligned (RTL)
                els.append(lab_el(lb, x, y0 + i * gap, t_note + i * 0.42, r=rot(1.5), depth=1.05))
        if st.get("tag"):
            els.append(El(KLabel(st["tag"], 44, YELLOW, seed=rs(), font="vazir", padx=26, pady=14).frame(10),
                          W - 190, mid - (380 if reel else 290), 9, t_note + 0.5, enter="pop", dur=0.5,
                          depth=1.3, seed=rs()))
        dur = max(3.4, t_note + 0.42 * len(notes) + 1.7)
        scenes.append(Scene(t0, dur, els, pans[(k + 1) % 4], lead=0.3))
        t0 += dur

    # ---- outro
    oc = spec["outro"]
    cy = (top + 230) if reel else (top + 150)
    els = [El(stamp, W / 2, cy - 100, -2, 0.0, enter="pop", dur=0.5, depth=0.7, seed=rs()),
           lab_el(label(oc["l1"], 86, YELLOW, font="vazir"), W / 2, cy + 115, 0.15),
           lab_el(label(oc["l2"], 50, WHITE, font="vazir"), W / 2, cy + 280, 0.45),
           lab_el(label(PHONE, 76, PINK, fg=WHITE, font="vazir"), W / 2, cy + 470, 0.75),
           lab_el(label(SITE, 50, CREAM, font="vazir"), W / 2, cy + 625, 0.95),
           El(draw_on(marker_arrow(200, 130, BLUE, seed=rs(), flip=True)), 150, cy + 570, 0, 1.2,
              own_time=True, seed=rs())]
    if oc.get("warranty"):
        els.append(lab_el(label(oc["warranty"], 44, SKY, font="vazir"), W / 2, cy + 775, 1.15))
    scenes.append(Scene(t0, 3.8, els, pans[(len(spec["steps"]) + 1) % 4], lead=0.3))
    t0 += 3.8
    return scenes, t0


# ------------------------------------------------------------------ render
STATE = {}


def make_static():
    big = paper_texture(int(W * 1.12), int(H * 1.12), KRAFT, seed=99, grain=12)
    vg = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vg).ellipse((-220, -220, W + 220, H + 220), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(170))
    vign = Image.new("RGBA", (W, H), (55, 35, 15, 255))
    vign.putalpha(Image.fromarray(255 - np.asarray(vg)).point(lambda v: v * 105 // 255))
    rng = np.random.default_rng(5)
    grains = [rng.normal(0, 5.5, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]
    grains = [np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR))[..., None] for g in grains]
    sheets = []
    for i, col in enumerate([CREAM, YELLOW, SKY, PINK]):
        sw, shh = int(W * 1.7), int(H * 1.5)
        sh = paper_texture(sw, shh, col, seed=200 + i, grain=7)
        sh.putalpha(torn_mask(sw, shh, 300 + i, rough=28, step=22))
        st = logo_stamp()
        sh.alpha_composite(st, ((sw - st.width) // 2, (shh - st.height) // 2))
        pad = 60
        full = Image.new("RGBA", (sw + 2 * pad, shh + 2 * pad), (0, 0, 0, 0))
        dark = Image.new("RGBA", sh.size, (40, 30, 20, 255))
        dark.putalpha(sh.getchannel("A").point(lambda v: v * 110 // 255))
        full.alpha_composite(dark, (pad + 14, pad + 20))
        full = cl.blur(full, 18)
        full.alpha_composite(sh, (pad, pad))
        sheets.append(full.rotate(-9 if i % 2 == 0 else 9, expand=True, resample=Image.BICUBIC))
    return big, vign, grains, sheets


def frame_at(T):
    scenes, total = STATE["scenes"], STATE["total"]
    big, vign, grains, sheets = STATE["static"]
    # background drifts slowly (whole film)
    q = T / max(total, 1)
    ox = int((big.width - W) / 2 + math.sin(q * math.pi * 1.3) * (big.width - W) * 0.4)
    oy = int((big.height - H) / 2 + math.cos(q * math.pi * 0.9) * (big.height - H) * 0.4)
    c = big.crop((ox, oy, ox + W, oy + H))
    # which scene is visible: switch at the middle of each wipe
    idx = 0
    for i, s in enumerate(scenes):
        if T >= s.start:
            idx = i
    scenes[idx].draw(c, T)
    # wipe around each boundary
    for i, s in enumerate(scenes[1:], start=1):
        b = s.start
        if b - WIPE <= T <= b + WIPE:
            p = in_out_cubic(pr(T, b - WIPE, 2 * WIPE))
            sh = sheets[(i - 1) % len(sheets)]
            d = 1 if i % 2 else -1
            cx = W / 2 + d * (1 - 2 * p) * (sh.width * 0.5 + W * 0.55)
            cy = H / 2 + (1 - 2 * p) * 120
            c.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)))
    c.alpha_composite(vign)
    arr = np.asarray(c.convert("RGB"), dtype=np.float32)
    arr = np.clip(arr + grains[int(T * FPS) // 2 % 4], 0, 255).astype(np.uint8)
    return arr


def _init(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    STATE["scenes"], STATE["total"] = build(spec, Path(spec_path).parent)
    STATE["static"] = make_static()


def _job(k):
    return frame_at(k / FPS).tobytes()


def main():
    spec_path, out = Path(sys.argv[1]), sys.argv[2]
    _init(spec_path)
    total = STATE["total"]
    if "--preview" in sys.argv:
        d = Path(sys.argv[sys.argv.index("--preview") + 1])
        d.mkdir(parents=True, exist_ok=True)
        times = [0.0, 0.5, 1.6]
        for s in STATE["scenes"][1:]:
            times += [s.start - 0.1, s.start + 0.6, s.start + s.dur - 0.5]
        for T in times:
            Image.fromarray(frame_at(T)).save(d / f"k_{T:05.2f}.jpg", quality=86)
        print(f"preview {len(times)} frames, {total:.1f}s")
        return
    n = int(total * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, min(4, __import__("os").cpu_count() or 1)), initializer=_init, initargs=(str(spec_path),)) as pool:
        for buf in pool.imap(_job, range(n), chunksize=6):
            proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    Image.fromarray(frame_at(1.6)).save(str(out).replace(".mp4", "-cover.jpg"), quality=92)
    print(f"{'reel' if H == 1920 else 'post'} {W}x{H} {total:.1f}s")


if __name__ == "__main__":
    main()
