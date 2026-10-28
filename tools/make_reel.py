"""Instagram Reel (1080x1920, 30fps) for lalehstore: new JBL / Infinity car audio.

Frames are rendered with PIL and piped straight into ffmpeg (silent AAC track
included so Instagram accepts it and lets you add music in-app).

Usage:
  python3 -I make_reel.py <src_dir> <vazirmatn_ttf_dir> <quicksand_bold.woff> <out.mp4> [--preview DIR]
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_post as mp  # noqa: E402
from make_wa import BLUE, NAVY, PINK, render_mark, render_wordmark  # noqa: E402

W, H = 1080, 1920
FPS = 30
XF = 0.30  # crossfade seconds between scenes
INK, MUTED, CARD, BG = mp.INK, mp.MUTED, mp.CARD, mp.BG


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.6):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def prog(t, start, dur):
    return clamp((t - start) / dur)


# ------------------------------------------------------------------ drawing
def with_alpha(im: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return im
    out = im.copy()
    out.putalpha(out.getchannel("A").point(lambda v: int(v * a)))
    return out


def place(canvas, im, cx, cy, alpha=1.0, scale=1.0, dy=0.0):
    """Paste `im` centred on (cx, cy) with alpha, scale and vertical offset."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BILINEAR)
    im = with_alpha(im, alpha)
    canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2 + dy)))


def make_background():
    bg = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((-420, -380, 640, 680), fill=PINK + (50,))
    g.ellipse((480, 1200, 1560, 2300), fill=BLUE + (50,))
    return bg, glow.convert("RGBa").filter(ImageFilter.GaussianBlur(220)).convert("RGBA")


def spotlight(w, h):
    s = Image.new("RGBA", (w + 300, h + 300), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((150, 150, w + 150, h + 150), fill=(255, 255, 255, 235))
    return s.convert("RGBa").filter(ImageFilter.GaussianBlur(80)).convert("RGBA")


def with_shadow(im, blur=28, opacity=70, offset=(0, 22)):
    s, pad = mp.shadow(im, blur=blur, opacity=opacity, offset=offset)
    s.alpha_composite(im, (pad, pad))
    return s


def pill(text, weight, px, fg, bg, padx=34, pady=16):
    t = mp.text_img(text, weight, px, fg)
    p = mp.rounded(t.width + padx * 2, t.height + pady * 2, (t.height + pady * 2) // 2, bg + (255,))
    p.alpha_composite(t, (padx, pady))
    return p


def gradient_pill(text, weight, px, padx=40, pady=20):
    t = mp.text_img(text, weight, px, (255, 255, 255))
    w, h = t.width + padx * 2, t.height + pady * 2
    g = mp.brand_gradient(w, h)
    g.putalpha(mp.rounded(w, h, h // 2, (255, 255, 255, 255)).getchannel("A"))
    g.alpha_composite(t, (padx, pady))
    return g


def logo_lockup(h):
    return mp.brand_lockup(h)


# ------------------------------------------------------------------ scenes
class Scene:
    duration = 3.0

    def draw(self, canvas, t):  # pragma: no cover
        raise NotImplementedError


class Intro(Scene):
    duration = 3.4

    def __init__(self, products):
        self.mark = render_mark(300)
        self.word = render_wordmark(mp.LATIN_FONT, 520)
        self.t1 = mp.text_img("رسید!", "Black", 150, INK)
        self.t2 = mp.gradient_text("سیستم صوتی خودرو", "Black", 92, rtl=True)
        self.t3 = mp.text_img("JBL  •  Infinity", "Black", 58, NAVY, rtl=False)
        self.thumbs = [with_shadow(mp.fit(p, 300, 300), blur=16, opacity=60, offset=(0, 12)) for p in products]
        self.spot = spotlight(1000, 600)

    def draw(self, c, t):
        # Phase A: logo pops in centre, then shrinks/moves up
        a = ease_back(prog(t, 0.0, 0.55))
        move = ease_out(prog(t, 0.85, 0.5))
        mark_y = 760 - move * 470
        mark_s = (1 - 0.55 * move) * a
        place(c, self.mark, W / 2, mark_y, alpha=clamp(a), scale=mark_s)
        wa = ease_out(prog(t, 0.3, 0.4)) * (1 - ease_out(prog(t, 0.8, 0.35)))
        place(c, self.word, W / 2, 1010, alpha=wa, dy=(1 - ease_out(prog(t, 0.3, 0.4))) * 30)

        # Phase B: headline
        for i, (im, y) in enumerate([(self.t1, 560), (self.t2, 730), (self.t3, 850)]):
            p = ease_out(prog(t, 1.05 + i * 0.14, 0.45))
            place(c, im, W / 2, y, alpha=p, dy=(1 - p) * 60)

        # Phase C: product thumbnails pop in a 2x2 grid
        p = ease_out(prog(t, 1.5, 0.4))
        place(c, self.spot, W / 2, 1275, alpha=p)
        pos = [(300, 1110), (780, 1110), (300, 1440), (780, 1440)]
        for i, (im, (x, y)) in enumerate(zip(self.thumbs, pos)):
            q = ease_back(prog(t, 1.55 + i * 0.12, 0.45))
            place(c, im, x, y, alpha=clamp(q), scale=0.6 + 0.4 * q)


class Product(Scene):
    duration = 3.3

    def __init__(self, img, kind, brand, model, specs, index, total):
        self.prod = with_shadow(mp.fit(img, 900, 560), blur=30, opacity=75)
        self.spot = spotlight(900, 560)
        self.kind = mp.text_img(kind, "Bold", 52, INK)
        self.brand = mp.gradient_text(brand, "Black", 42, rtl=False)
        model_px = 104 if len(model) <= 10 else 84
        self.model = mp.text_img(model, "Black", model_px, INK, rtl=False)
        self.tag = pill("جدید", "Bold", 32, (255, 255, 255), NAVY)
        self.counter = mp.text_img(f"{index} / {total}", "Bold", 30, MUTED, rtl=False)
        cw = (W - 128 - 2 * 22) // 3
        self.chips = [with_shadow(mp.chip(l, v, cw), blur=18, opacity=30, offset=(0, 8)) for l, v in specs]
        self.cw = cw

    def draw(self, c, t):
        p = ease_out(prog(t, 0.0, 0.45))
        place(c, self.tag, W / 2 - 80, 380, alpha=p, scale=0.8 + 0.2 * p)
        place(c, self.counter, W / 2 + 80, 380, alpha=p)
        for i, (im, y) in enumerate([(self.kind, 480), (self.brand, 560), (self.model, 645)]):
            q = ease_out(prog(t, 0.08 + i * 0.1, 0.45))
            place(c, im, W / 2, y, alpha=q, dy=(1 - q) * 50)

        q = ease_out(prog(t, 0.15, 0.6))
        place(c, self.spot, W / 2, 1050, alpha=q)
        zoom = 0.86 + 0.14 * q + 0.04 * prog(t, 0.6, self.duration)
        place(c, self.prod, W / 2, 1050, alpha=q, scale=zoom)

        x = W - 64 - self.cw / 2
        for i, ch in enumerate(self.chips):
            r = ease_back(prog(t, 0.6 + i * 0.16, 0.45))
            place(c, ch, x - i * (self.cw + 22), 1470, alpha=clamp(r), scale=0.7 + 0.3 * r)


class Outro(Scene):
    duration = 4.2

    def __init__(self):
        self.logo = logo_lockup(84)
        self.t1 = mp.text_img("استعلام قیمت و سفارش", "Black", 70, INK)
        self.t2 = mp.text_img("دایرکت بده یا تماس بگیر", "Medium", 40, MUTED)
        self.phone = mp.gradient_text("021-33917554", "Black", 96, rtl=False)
        self.site = mp.text_img("lalehstore.com", "Bold", 50, NAVY, rtl=False)
        self.badges = [
            pill("12 ماه ضمانت صوت ایران کیش", "Bold", 34, INK, CARD),
            pill("تضمین اصالت کالا", "Bold", 34, INK, CARD),
            pill("ارسال سریع با پیک و تیپاکس", "Bold", 34, INK, CARD),
        ]
        self.badges = [with_shadow(b, blur=16, opacity=26, offset=(0, 8)) for b in self.badges]
        self.cta = gradient_pill("همین حالا دایرکت بده", "Black", 40)

    def draw(self, c, t):
        p = ease_back(prog(t, 0.0, 0.5))
        place(c, self.logo, W / 2, 360, alpha=clamp(p), scale=0.7 + 0.3 * p)
        for i, (im, y) in enumerate([(self.t1, 540), (self.t2, 630)]):
            q = ease_out(prog(t, 0.2 + i * 0.1, 0.45))
            place(c, im, W / 2, y, alpha=q, dy=(1 - q) * 50)
        q = ease_back(prog(t, 0.45, 0.5))
        place(c, self.phone, W / 2, 770, alpha=clamp(q), scale=0.8 + 0.2 * q)
        q = ease_out(prog(t, 0.6, 0.45))
        place(c, self.site, W / 2, 880, alpha=q, dy=(1 - q) * 30)
        for i, b in enumerate(self.badges):
            r = ease_back(prog(t, 0.85 + i * 0.15, 0.45))
            place(c, b, W / 2, 1040 + i * 120, alpha=clamp(r), scale=0.75 + 0.25 * r)
        r = ease_back(prog(t, 1.5, 0.5))
        pulse = 1 + 0.035 * math.sin(max(0.0, t - 2.0) * 2 * math.pi / 1.1) * (t > 2.0)
        place(c, self.cta, W / 2, 1450, alpha=clamp(r), scale=(0.7 + 0.3 * r) * pulse)


# ------------------------------------------------------------------ timeline
def build(src: Path):
    club = mp.trim(Image.open(src / "jbl-club-64c.webp").convert("RGBA"))
    gx = mp.trim(Image.open(src / "jbl-gx9638-3.webp").convert("RGBA"))
    inf = mp.trim(mp.remove_white_bg(Image.open(src / "Infinity-Reference-6530cx.webp")))
    sub = mp.trim(Image.open(src / "JBL_Stage_122.webp").convert("RGBA"))
    n = 4
    return [
        Intro([club, gx, inf, sub]),
        Product(club, "کامپوننت 16 سانت 2Way", "JBL", "Club 64C",
                [("توان نامی", "70W"), ("حساسیت", "92dB"), ("امپدانس", "3 Ohm")], 1, n),
        Product(gx, "باند بیضی 6×9 سه راهه (3Way)", "JBL", "GX9638",
                [("توان نامی", "100W"), ("حساسیت", "94dB"), ("پاسخ فرکانسی", "45Hz")], 2, n),
        Product(inf, "کامپوننت 16 سانت 2Way", "Infinity", "Reference 6530CX",
                [("توان نامی", "90W"), ("حساسیت", "93dB"), ("امپدانس", "3 Ohm")], 3, n),
        Product(sub, "ساب ووفر 12 اینچ", "JBL", "Stage 122",
                [("توان نامی", "250W"), ("حداکثر توان", "1000W"), ("پاسخ فرکانسی", "34Hz")], 4, n),
        Outro(),
    ]


def main():
    args = sys.argv[1:]
    preview = None
    if "--preview" in args:
        i = args.index("--preview")
        preview = Path(args[i + 1])
        del args[i:i + 2]
    src, mp.FONT_DIR, mp.LATIN_FONT, out = args[:4]
    src = Path(src)

    scenes = build(src)
    bg, glow = make_background()
    base = bg.copy()
    base.alpha_composite(glow)

    starts, t0 = [], 0.0
    for s in scenes:
        starts.append(t0)
        t0 += s.duration - XF
    total = t0 + XF
    nframes = round(total * FPS)

    def scene_layer(i, t):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        scenes[i].draw(layer, t)
        return layer

    def frame(T):
        canvas = base.copy()
        active = [i for i, s in enumerate(scenes) if starts[i] <= T < starts[i] + s.duration]
        for i in active:
            lt = T - starts[i]
            a = 1.0
            if i < len(scenes) - 1 and lt > scenes[i].duration - XF:
                a = 1 - (lt - (scenes[i].duration - XF)) / XF
            layer = scene_layer(i, lt)
            canvas.alpha_composite(with_alpha(layer, a))
        # persistent footer brand mark (small, top-centre) except during intro logo
        return canvas.convert("RGB")

    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        for k, T in enumerate([0.4, 1.0, 2.6, 4.6, 7.6, 10.6, 13.8, 15.2, 16.6, total - 0.05]):
            frame(T).save(preview / f"f{k:02d}_{T:.1f}.jpg", quality=85)
        print(f"preview written, total {total:.1f}s")
        return

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(nframes):
        proc.stdin.write(frame(k / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"done: {nframes} frames, {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()
