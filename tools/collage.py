"""lalehstore paper-collage motion renderer (stop-motion style).

Renders a reel (1080x1920) or a feed post video (1080x1350) from a JSON spec:

{
  "format": "reel" | "post",
  "hook":  {"l1": "کدوم مودم", "l2": "برای خونه تو؟", "sub": "راهنمای انتخاب مودم",
            "images": ["img1.png", "img2.png", "img3.png"]},
  "steps": [
    {"title": "خط تلفنت ADSL هست؟",
     "products": [{"img": "a.webp", "caption": "TD-W8961N"}, {"img": "b.webp", "caption": "DSL-124"}],
     "notes": ["سرعت وای فای تا 300Mbps", "36 ماه ضمانت"],
     "tag": "انتخاب خوب"}
  ],
  "outro": {"l1": "نمی دونی خطت چیه؟", "l2": "دایرکت بده تا راهنماییت کنیم", "warranty": "36 ماه ضمانت"}
}

Usage:
  python3 -I collage.py spec.json out.mp4 [--preview DIR]
Fonts are read from ./fonts (run setup.sh once).
"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_post as mp  # noqa: E402
from make_wa import BLUE, NAVY, PINK, render_mark  # noqa: E402

FPS, STEP, SS = 30, 3, 2
INK = (30, 28, 34)
KRAFT = (214, 190, 150)
CREAM = (250, 244, 228)
YELLOW = (255, 222, 89)
SKY = (226, 238, 255)
WHITE = (255, 255, 255)
COLORS = {"yellow": YELLOW, "pink": PINK, "cream": CREAM, "white": WHITE, "blue": SKY}
PHONE, SITE = "021-33917554", "lalehstore.com"
W, H = 1080, 1920
LALEZAR = str(HERE / "fonts" / "lalezar-arabic-400-normal.woff")
mp.FONT_DIR = str(HERE / "fonts")
mp.LATIN_FONT = str(HERE / "fonts" / "quicksand-latin-700-normal.woff")


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eb(x, s=2.0):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def pr(t, a, d):
    return clamp((t - a) / d)


def blur(im, r):
    return im.convert("RGBa").filter(ImageFilter.GaussianBlur(r)).convert("RGBA")


# ------------------------------------------------------------------ paper bits
def paper_texture(w, h, base, seed=1, grain=10):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, grain, (max(1, h // 2), max(1, w // 2)))
    n = np.asarray(Image.fromarray(n.astype(np.float32)).resize((w, h), Image.BILINEAR))
    fib = rng.normal(0, 1, (h, max(1, w // 8)))
    fib = np.asarray(Image.fromarray(fib.astype(np.float32)).resize((w, h), Image.BILINEAR)) * 4
    arr = np.clip(np.array(base, np.float32)[None, None] + (n + fib)[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def torn_mask(w, h, seed, rough=10, step=14):
    rnd = random.Random(seed)
    pts = []
    for x in range(0, w + 1, step):
        pts.append((x, rnd.uniform(0, rough)))
    for y in range(0, h + 1, step):
        pts.append((w - rnd.uniform(0, rough * 0.6), y))
    for x in range(w, -1, -step):
        pts.append((x, h - rnd.uniform(0, rough)))
    for y in range(h, -1, -step):
        pts.append((rnd.uniform(0, rough * 0.6), y))
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return m.resize((w, h), Image.LANCZOS)


def drop_shadow(im, r=10, off=(8, 12), a=90):
    pad = r * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (40, 30, 20, 255))
    sh.putalpha(im.getchannel("A").point(lambda v: v * a // 255))
    out.alpha_composite(sh, (pad + off[0], pad + off[1]))
    out = blur(out, r)
    out.alpha_composite(im, (pad, pad))
    return out


def _is_persian_only(text):
    """Lalezar (Arabic subset) has no Latin letters, digits or ASCII punctuation."""
    return not any(ch.isascii() and not ch.isspace() for ch in text)


def _render_text(text, px, fg, font):
    if font == "lalezar" and _is_persian_only(text):
        f = ImageFont.truetype(LALEZAR, px * SS, layout_engine=ImageFont.Layout.RAQM)
        layer = Image.new("RGBA", (len(text) * px * SS + 200, px * SS * 3), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((layer.width // 2, layer.height // 2), text, font=f, fill=fg + (255,),
                                   anchor="mm", direction="rtl")
        layer = layer.crop(layer.getchannel("A").getbbox())
        return layer.resize((layer.width // SS, layer.height // SS), Image.LANCZOS)
    rtl = any("؀" <= ch <= "ۿ" for ch in text)
    return mp.text_img(text, "Black", px, fg, rtl=rtl)


def torn_label(text, px, bg, fg=INK, seed=3, font="lalezar", padx=46, pady=26, max_w=None):
    max_w = max_w or W - 90
    t = _render_text(text, px, fg, font)
    while t.width + 2 * padx > max_w and px > 24:
        px = int(px * 0.9)
        t = _render_text(text, px, fg, font)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    p = paper_texture(w, h, bg, seed=seed, grain=6)
    p.putalpha(torn_mask(w, h, seed))
    p.alpha_composite(t, (padx, pady))
    return drop_shadow(p, r=8, off=(6, 9), a=80)


def tape(w=190, h=56, seed=5, angle=0):
    rnd = random.Random(seed)
    body = paper_texture(w, h, (238, 226, 190), seed=seed, grain=4)
    m = Image.new("L", (w, h), 0)
    pts = []
    for y in range(0, h + 1, 7):
        pts.append((rnd.uniform(0, 7), y))
    for y in range(h, -1, -7):
        pts.append((w - rnd.uniform(0, 7), y))
    ImageDraw.Draw(m).polygon(pts, fill=205)
    body.putalpha(m)
    return body.rotate(angle, expand=True, resample=Image.BICUBIC)


def load_img(path):
    return Image.open(path).convert("RGBA")


def polaroid(photo, w=420, seed=7, caption=None):
    inner = w - 44
    ph = mp.fit(photo, inner, inner)
    box = Image.new("RGBA", (inner, inner), (255, 255, 255, 255))
    box.alpha_composite(ph, ((inner - ph.width) // 2, (inner - ph.height) // 2))
    cap_h = 90 if caption else 40
    card = paper_texture(w, inner + 44 + cap_h - 22, (252, 251, 247), seed=seed, grain=3)
    card.alpha_composite(box, (22, 22))
    if caption:
        rtl = any("؀" <= ch <= "ۿ" for ch in caption)
        c = mp.text_img(caption, "Black", 40, INK, rtl=rtl)
        c = mp.fit(c, w - 40, 60) if c.width > w - 40 else c
        card.alpha_composite(c, ((w - c.width) // 2, inner + 22 + (cap_h - c.height) // 2 - 6))
    return drop_shadow(card, r=10, off=(8, 12), a=90)


def marker_arrow(w=220, h=150, color=PINK, seed=9, flip=False):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(14):
        k = i / 13
        x = 20 + k * (w - 60)
        y = h - 30 - math.sin(k * math.pi) * (h - 70) + rnd.uniform(-2, 2)
        pts.append((x * SS, y * SS))
    d.line(pts, fill=color + (255,), width=9 * SS, joint="curve")
    ex, ey = pts[-1]
    d.line([(ex, ey), (ex - 34 * SS, ey - 20 * SS)], fill=color + (255,), width=9 * SS)
    d.line([(ex, ey), (ex - 10 * SS, ey + 34 * SS)], fill=color + (255,), width=9 * SS)
    im = im.resize((w, h), Image.LANCZOS)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def note_card(lines, w=620, seed=13, bg=CREAM):
    imgs = []
    for l in lines:
        im = mp.text_img(l, "Bold", 36, INK)
        imgs.append(mp.fit(im, w - 70, 60) if im.width > w - 70 else im)
    lh = 64
    h = 50 + lh * len(lines)
    card = paper_texture(w, h, bg, seed=seed, grain=4)
    d = ImageDraw.Draw(card)
    for i in range(len(lines) + 1):
        y = 34 + i * lh
        d.line([(24, y + 46), (w - 24, y + 46)], fill=(150, 180, 220, 120), width=2)
    for i, im in enumerate(imgs):
        card.alpha_composite(im, (w - 34 - im.width, 26 + i * lh + (lh - im.height) // 2))
    card.putalpha(torn_mask(w, h, seed, rough=6))
    return drop_shadow(card, r=8, off=(6, 9), a=80)


def logo_stamp():
    mark = mp.fit(mp.trim(render_mark(60)), 10_000, 56)
    word = mp.text_img("lalehstore", "Black", 34, INK, rtl=False)
    w, h = mark.width + word.width + 60, 86
    p = paper_texture(w, h, WHITE, seed=21, grain=3)
    p.putalpha(torn_mask(w, h, 21, rough=5))
    p.alpha_composite(mark, (20, (h - mark.height) // 2))
    p.alpha_composite(word, (20 + mark.width + 14, (h - word.height) // 2))
    return drop_shadow(p, r=6, off=(4, 6), a=70)


# ------------------------------------------------------------------ stage
class Piece:
    def __init__(self, img, x, y, rot, t_in, seed, jitter=1.2, instant=False):
        self.img, self.x, self.y, self.rot, self.t_in = img, x, y, rot, t_in
        self.seed, self.jitter, self.instant = seed, jitter, instant
        self.cache = {}

    def draw(self, c, t, t_out):
        if t < self.t_in:
            return
        p = 1.0 if self.instant else eb(pr(t, self.t_in, 0.35))
        tick = int(t * FPS) // STEP
        rnd = random.Random(self.seed * 1000 + tick)
        rot = self.rot + rnd.uniform(-self.jitter, self.jitter) + (1 - p) * 18
        jx, jy = rnd.uniform(-2.5, 2.5), rnd.uniform(-2.5, 2.5)
        s = 1.25 - 0.25 * p
        a = clamp(p * 1.5)
        if t > t_out:
            q = pr(t, t_out, 0.25)
            a *= 1 - q
            jy += q * 220
        if a <= 0.01:
            return
        key = (round(rot, 1), round(s, 2))
        im = self.cache.get(key)
        if im is None:
            im = self.img.rotate(rot, expand=True, resample=Image.BICUBIC)
            if abs(s - 1) > 0.01:
                im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            if len(self.cache) < 400:
                self.cache[key] = im
        if a < 0.999:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(im, (int(self.x - im.width / 2 + jx), int(self.y + jy - im.height / 2)))


class Scene:
    def __init__(self, start, end, pieces):
        self.start, self.end, self.pieces = start, end, pieces

    def draw(self, c, t):
        if self.start <= t < self.end + 0.3:
            for pc in self.pieces:
                pc.draw(c, t - self.start, (self.end - self.start) - 0.05)


# ------------------------------------------------------------------ template
def build(spec, base_dir: Path):
    global W, H
    W, H = (1080, 1920) if spec.get("format", "reel") == "reel" else (1080, 1350)
    reel = H == 1920
    top = 250 if reel else 110          # logo stamp y
    seed = random.Random(spec.get("seed", 7))
    rs = lambda: seed.randint(1, 10_000)  # noqa: E731
    rot = lambda m=3.0: seed.uniform(-m, m)  # noqa: E731
    img = lambda p: load_img(base_dir / p)  # noqa: E731
    stamp = logo_stamp()

    scenes, t0 = [], 0.0
    # ---- hook (text visible in frame 1)
    hk = spec["hook"]
    pcs = [Piece(stamp, 230, top, -3, 0, rs(), jitter=0.6, instant=True),
           Piece(torn_label(hk["l1"], 130, YELLOW, seed=rs()), W / 2, top + 230, rot(), 0, rs(), instant=True),
           Piece(torn_label(hk["l2"], 118, PINK, fg=WHITE, seed=rs()), W / 2, top + 420, rot(), 0, rs(), instant=True)]
    if hk.get("sub"):
        pcs.append(Piece(torn_label(hk["sub"], 46, CREAM, seed=rs(), font="vazir"), W / 2, top + 575, rot(2), 0.3, rs()))
    ims = hk.get("images", [])[:4]
    n = len(ims)
    if n:
        pw = 330 if n >= 3 else 420
        ys = (top + 1010) if reel else (top + 820)
        xs = {1: [W / 2], 2: [320, 760], 3: [215, 540, 865], 4: [300, 780, 300, 780]}[n]
        for i, p in enumerate(ims):
            y = ys if n < 4 else (ys - 180 + (i // 2) * 420 if reel else ys - 120 + (i // 2) * 330)
            pw_i = pw if n < 4 else (380 if reel else 300)
            pcs.append(Piece(polaroid(img(p), pw_i, seed=rs()), xs[i], y + seed.uniform(-30, 30), rot(8), 0.45 + i * 0.18, rs()))
            pcs.append(Piece(tape(170, 52, seed=rs(), angle=rot(14)), xs[i], y - pw_i * 0.55, 0, 0.55 + i * 0.18, rs(), jitter=0.4))
        pcs.append(Piece(marker_arrow(230, 150, BLUE, seed=rs()), W - 220, top + 560 if not hk.get("sub") else top + 640,
                         0, 1.3, rs(), jitter=0.8))
    scenes.append(Scene(t0, t0 + 3.4, pcs))
    t0 += 3.4

    # ---- steps
    for k, st in enumerate(spec["steps"]):
        pcs = [Piece(stamp, 230, top, -3, 0, rs(), jitter=0.6, instant=True),
               Piece(torn_label(st["title"], 70, CREAM if k % 2 == 0 else SKY, seed=rs(), font="vazir"),
                     W / 2, top + 170, rot(2), 0.0, rs())]
        prods = st.get("products", [])[:2]
        mid = (top + 720) if reel else (top + 560)
        if len(prods) == 1:
            pw = 600 if reel else 520
            pcs.append(Piece(polaroid(img(prods[0]["img"]), pw, seed=rs(), caption=prods[0].get("caption")),
                             W / 2, mid, rot(4), 0.25, rs()))
            pcs.append(Piece(tape(210, 60, seed=rs(), angle=rot(8)), W / 2, mid - pw * 0.62, 0, 0.35, rs(), jitter=0.4))
        elif len(prods) == 2:
            pw = 470 if reel else 430
            for i, (pd, x) in enumerate(zip(prods, (W * 0.70, W * 0.30))):  # RTL: first on the right
                y = mid + (0 if i == 0 else 50)
                pcs.append(Piece(polaroid(img(pd["img"]), pw, seed=rs(), caption=pd.get("caption")),
                                 x, y, rot(6), 0.25 + i * 0.2, rs()))
                pcs.append(Piece(tape(190, 56, seed=rs(), angle=rot(12)), x, y - pw * 0.62, 0, 0.35 + i * 0.2, rs(), jitter=0.4))
        if st.get("notes"):
            ny = (H - 560) if reel else (H - 190)
            nb = CREAM if k % 2 else SKY
            pcs.append(Piece(note_card(st["notes"], 640, seed=rs(), bg=nb), W / 2, ny, rot(2), 0.9, rs()))
        if st.get("tag"):
            pcs.append(Piece(torn_label(st["tag"], 44, YELLOW, seed=rs(), font="vazir", padx=26, pady=14),
                             W - 190, mid - (380 if reel else 300), 9, 1.4, rs()))
        dur = 3.8 if st.get("notes") else 3.4
        scenes.append(Scene(t0, t0 + dur, pcs))
        t0 += dur

    # ---- outro
    oc = spec["outro"]
    cy = (top + 230) if reel else (top + 160)
    pcs = [Piece(stamp, W / 2, cy - 100, -2, 0, rs(), jitter=0.6),
           Piece(torn_label(oc["l1"], 88, YELLOW, seed=rs(), font="vazir"), W / 2, cy + 120, rot(2), 0.1, rs()),
           Piece(torn_label(oc["l2"], 52, WHITE, seed=rs(), font="vazir"), W / 2, cy + 290, rot(2), 0.35, rs()),
           Piece(torn_label(PHONE, 78, PINK, fg=WHITE, seed=rs(), font="vazir"), W / 2, cy + 490, rot(1.5), 0.6, rs()),
           Piece(torn_label(SITE, 52, CREAM, seed=rs(), font="vazir"), W / 2, cy + 650, rot(2), 0.8, rs()),
           Piece(marker_arrow(200, 130, BLUE, seed=rs(), flip=True), 150, cy + 590, 0, 1.0, rs())]
    if oc.get("warranty"):
        pcs.append(Piece(torn_label(oc["warranty"], 44, SKY, seed=rs(), font="vazir"), W / 2, cy + 800, rot(3), 1.1, rs()))
    scenes.append(Scene(t0, t0 + 3.8, pcs))
    t0 += 3.8
    return scenes, t0


def render(scenes, total, out_mp4=None, preview_dir=None):
    bg = paper_texture(W, H, KRAFT, seed=99, grain=12)
    vg = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vg).ellipse((-200, -200, W + 200, H + 200), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (60, 40, 20, 255))
    dark.putalpha(Image.fromarray(255 - np.asarray(vg)).point(lambda v: v * 90 // 255))
    bg.alpha_composite(dark)

    def frame(T):
        c = bg.copy()
        for s in scenes:
            s.draw(c, T)
        return c.convert("RGB")

    if preview_dir:
        Path(preview_dir).mkdir(parents=True, exist_ok=True)
        times = [0.0, 1.8] + [s.start + 1.9 for s in scenes[1:]]
        for T in times:
            frame(T).save(Path(preview_dir) / f"c_{T:05.2f}.jpg", quality=86)
        return
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out_mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last, last_tick = None, None
    for k in range(int(total * FPS)):
        tick = k // STEP
        if tick != last_tick:
            last, last_tick = frame(tick * STEP / FPS), tick
        proc.stdin.write(last.tobytes())
    proc.stdin.close()
    proc.wait()
    frame(1.8).save(str(out_mp4).replace(".mp4", "-cover.jpg"), quality=92)


def main():
    spec_path, out = Path(sys.argv[1]), sys.argv[2]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    scenes, total = build(spec, spec_path.parent)
    if "--preview" in sys.argv:
        render(scenes, total, preview_dir=sys.argv[sys.argv.index("--preview") + 1])
    else:
        render(scenes, total, out_mp4=out)
    print(f"{spec.get('format', 'reel')} {W}x{H} {total:.1f}s")


if __name__ == "__main__":
    main()
