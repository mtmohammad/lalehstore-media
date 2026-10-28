"""Instagram carousel (1080x1350) for lalehstore: new JBL / Infinity car audio.

Usage:
  python3 -I make_post.py <src_dir> <vazirmatn_ttf_dir> <quicksand_bold.woff> <out_dir>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_wa import BLUE, NAVY, PINK, render_mark, render_wordmark  # noqa: E402

W, H = 1080, 1350
BG = (246, 247, 251)
INK = (28, 30, 42)
MUTED = (110, 114, 132)
CARD = (255, 255, 255)
SS = 3

FONT_DIR = ""
LATIN_FONT = ""


def font(weight: str, px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        f"{FONT_DIR}/Vazirmatn-{weight}.ttf", px, layout_engine=ImageFont.Layout.RAQM
    )


# ----------------------------------------------------------------- helpers
def remove_white_bg(im: Image.Image, thresh: int = 238) -> Image.Image:
    """Make the white background that touches the image border transparent."""
    im = im.convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    white = (a[..., :3].min(-1) >= thresh)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgmask = np.isin(lab, list(border))
    alpha = np.where(bgmask, 0, 255).astype(np.uint8)
    alpha = np.asarray(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2)))
    out = np.asarray(im).copy()
    out[..., 3] = np.minimum(out[..., 3], alpha)
    return Image.fromarray(out, "RGBA")


def trim(im: Image.Image) -> Image.Image:
    return im.crop(im.getchannel("A").getbbox())


def fit(im: Image.Image, box_w: int, box_h: int) -> Image.Image:
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def text_img(text: str, fnt_weight: str, px: int, color, rtl=True) -> Image.Image:
    f = font(fnt_weight, px * SS)
    layer = Image.new("RGBA", (len(text) * px * SS + 400, px * SS * 3), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (layer.width // 2, layer.height // 2), text, font=f, fill=tuple(color) + (255,),
        anchor="mm", direction="rtl" if rtl else "ltr",
    )
    layer = trim(layer)
    return layer.resize((max(1, layer.width // SS), max(1, layer.height // SS)), Image.LANCZOS)


def gradient_text(text: str, weight: str, px: int, rtl=False) -> Image.Image:
    """Text filled with the brand pink→blue gradient."""
    t = text_img(text, weight, px, (0, 0, 0), rtl=rtl)
    grad = brand_gradient(t.width, t.height)
    grad.putalpha(t.getchannel("A"))
    return grad


def brand_gradient(w: int, h: int) -> Image.Image:
    x = np.linspace(0, 1, w)[None, :, None]
    c = np.array(PINK)[None, None, :] * (1 - x) + np.array(BLUE)[None, None, :] * x
    c = np.repeat(c, h, axis=0)
    return Image.fromarray(c.astype(np.uint8), "RGB").convert("RGBA")


def rounded(w: int, h: int, r: int, fill) -> Image.Image:
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=fill)
    return big.resize((w, h), Image.LANCZOS)


def shadow(im: Image.Image, blur: int = 30, opacity: int = 60, offset=(0, 18)) -> Image.Image:
    pad = blur * 3
    s = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: v * opacity // 255)
    blk = Image.new("RGBA", im.size, (20, 22, 40, 255))
    blk.putalpha(a)
    s.alpha_composite(blk, (pad + offset[0], pad + offset[1]))
    return s.filter(ImageFilter.GaussianBlur(blur)), pad


def paste_with_shadow(canvas, im, x, y, **kw):
    s, pad = shadow(im, **kw)
    canvas.alpha_composite(s, (x - pad, y - pad))
    canvas.alpha_composite(im, (x, y))


def background() -> Image.Image:
    bg = Image.new("RGBA", (W, H), BG + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((-380, -380, 560, 560), fill=PINK + (46,))
    g.ellipse((560, 760, 1500, 1700), fill=BLUE + (46,))
    bg.alpha_composite(glow.convert("RGBa").filter(ImageFilter.GaussianBlur(190)).convert("RGBA"))
    return bg


def brand_lockup(height: int) -> Image.Image:
    """Small horizontal logo: mark + wordmark."""
    mark = trim(render_mark(int(height * 1.05)))
    mark = fit(mark, 10_000, height)
    word = render_wordmark(LATIN_FONT, int(height * 3.6))
    word = fit(word, 10_000, int(height * 0.62))
    gap = int(height * 0.28)
    out = Image.new("RGBA", (mark.width + gap + word.width, height), (0, 0, 0, 0))
    out.alpha_composite(mark, (0, 0))
    out.alpha_composite(word, (mark.width + gap, (height - word.height) // 2 + 2))
    return out


def header(canvas: Image.Image, page: int, total: int) -> None:
    logo = brand_lockup(58)
    canvas.alpha_composite(logo, (64, 60))
    # page indicator on the right (RTL reading start)
    dots_w = total * 14 + (total - 1) * 10 + 22
    x = W - 64 - dots_w
    d = ImageDraw.Draw(canvas)
    for i in range(total):
        active = i == total - page  # rightmost = first page
        w = 36 if active else 14
        col = (PINK if active else (205, 208, 220)) + (255,)
        d.rounded_rectangle((x, 82, x + w, 96), 7, fill=col)
        x += w + 10


def footer_bar(canvas: Image.Image) -> None:
    bar_h = 118
    bar = brand_gradient(W, bar_h)
    canvas.alpha_composite(bar, (0, H - bar_h))
    left = text_img("lalehstore.com", "Bold", 34, (255, 255, 255), rtl=False)
    canvas.alpha_composite(left, (64, H - bar_h + (bar_h - left.height) // 2))
    right = text_img("12 ماه ضمانت صوت ایران کیش", "Bold", 32, (255, 255, 255))
    canvas.alpha_composite(right, (W - 64 - right.width, H - bar_h + (bar_h - right.height) // 2))


def chip(label: str, value: str, w: int) -> Image.Image:
    h = 148
    c = rounded(w, h, 28, CARD + (255,))
    v = text_img(value, "Black", 46, INK, rtl=False)
    l = text_img(label, "Medium", 25, MUTED)
    c.alpha_composite(v, ((w - v.width) // 2, 30))
    c.alpha_composite(l, ((w - l.width) // 2, 30 + v.height + 22))
    return c


# ----------------------------------------------------------------- slides
def product_slide(page, total, product_img, kind, brand, model, specs, tag="جدید"):
    c = background()
    header(c, page, total)

    # Tag pill (top right, under dots)
    tg = text_img(tag, "Bold", 28, (255, 255, 255))
    pill = rounded(tg.width + 56, tg.height + 30, (tg.height + 30) // 2, NAVY + (255,))
    pill.alpha_composite(tg, (28, 15))
    c.alpha_composite(pill, (W - 64 - pill.width, 160))

    # Category (Persian) + model (Latin)
    k = text_img(kind, "Bold", 44, INK)
    c.alpha_composite(k, (W - 64 - k.width, 250))
    b = gradient_text(brand, "Black", 34, rtl=False)
    c.alpha_composite(b, (W - 64 - b.width, 330))
    m = text_img(model, "Black", 84, INK, rtl=False)
    c.alpha_composite(m, (W - 64 - m.width, 382))

    # Product with soft spotlight
    spot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(spot).ellipse((170, 520, 910, 1000), fill=(255, 255, 255, 230))
    c.alpha_composite(spot.convert("RGBa").filter(ImageFilter.GaussianBlur(70)).convert("RGBA"))
    p = fit(product_img, 760, 470)
    paste_with_shadow(c, p, (W - p.width) // 2, 505 + (470 - p.height) // 2, blur=26, opacity=70)

    # Spec chips
    n = len(specs)
    gap = 22
    cw = (W - 128 - gap * (n - 1)) // n
    x = W - 64 - cw
    for label, value in specs:  # right-to-left order
        ch = chip(label, value, cw)
        paste_with_shadow(c, ch, x, 1032, blur=18, opacity=28, offset=(0, 8))
        x -= cw + gap

    footer_bar(c)
    return c


def cover_slide(total, imgs):
    c = background()
    header(c, 1, total)

    t1 = text_img("رسید!", "Black", 120, INK)
    c.alpha_composite(t1, (W - 64 - t1.width, 175))
    t2 = gradient_text("سیستم صوتی خودرو", "Black", 78, rtl=True)
    c.alpha_composite(t2, (W - 64 - t2.width, 345))
    t3 = text_img("JBL  •  Infinity", "Black", 48, NAVY, rtl=False)
    c.alpha_composite(t3, (W - 64 - t3.width, 475))
    t4 = text_img("کامپوننت، باند و ساب ووفر اورجینال", "Medium", 34, MUTED)
    c.alpha_composite(t4, (W - 64 - t4.width, 560))

    spot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(spot).ellipse((90, 660, 990, 1210), fill=(255, 255, 255, 230))
    c.alpha_composite(spot.convert("RGBa").filter(ImageFilter.GaussianBlur(70)).convert("RGBA"))

    sub, gx, comp, inf = imgs
    # collage: sub back-left, 6x9 back-right, components in front
    a = fit(sub, 400, 400)
    paste_with_shadow(c, a, 90, 650, blur=24, opacity=60)
    b = fit(gx, 470, 340)
    paste_with_shadow(c, b, W - 90 - b.width, 650, blur=24, opacity=60)
    d = fit(inf, 520, 300)
    paste_with_shadow(c, d, 60, 905, blur=24, opacity=70)
    e = fit(comp, 470, 300)
    paste_with_shadow(c, e, W - 70 - e.width, 925, blur=24, opacity=70)

    footer_bar(c)
    return c


def final_slide(total, page):
    c = background()
    header(c, page, total)

    t1 = text_img("چرا لاله استور؟", "Black", 76, INK)
    c.alpha_composite(t1, (W - 64 - t1.width, 200))

    items = [
        ("12 ماه ضمانت صوت ایران کیش", "روی تمام محصولات JBL و Infinity"),
        ("تضمین اصالت کالا", "محصولات اورجینال تحت لیسانس آمریکا"),
        ("ارسال سریع", "ارسال با پیک و تیپاکس به سراسر ایران"),
        ("مشاوره رایگان", "برای انتخاب سیستم مناسب خودروی شما"),
    ]
    y = 345
    for i, (title, sub) in enumerate(items):
        card = rounded(W - 128, 138, 30, CARD + (255,))
        num = rounded(78, 78, 24, (0, 0, 0, 0))
        g = brand_gradient(78, 78)
        g.putalpha(rounded(78, 78, 24, (255, 255, 255, 255)).getchannel("A"))
        n = text_img(str(i + 1), "Black", 38, (255, 255, 255), rtl=False)
        g.alpha_composite(n, ((78 - n.width) // 2, (78 - n.height) // 2))
        card.alpha_composite(g, (card.width - 30 - 78, 30))
        tt = text_img(title, "Bold", 38, INK)
        st = text_img(sub, "Medium", 27, MUTED)
        rx = card.width - 30 - 78 - 28
        card.alpha_composite(tt, (rx - tt.width, 26))
        card.alpha_composite(st, (rx - st.width, 26 + tt.height + 18))
        paste_with_shadow(c, card, 64, y, blur=18, opacity=26, offset=(0, 8))
        y += 138 + 26

    # contact block
    cta = text_img("استعلام قیمت و سفارش", "Black", 46, INK)
    c.alpha_composite(cta, (W - 64 - cta.width, 1030))
    dm = text_img("دایرکت بده یا تماس بگیر", "Medium", 30, MUTED)
    c.alpha_composite(dm, (W - 64 - dm.width, 1098))
    ph = gradient_text("021-33917554", "Black", 54, rtl=False)
    c.alpha_composite(ph, (64, 1040))

    footer_bar(c)
    return c


def main():
    global FONT_DIR, LATIN_FONT
    src, FONT_DIR, LATIN_FONT, out = sys.argv[1:5]
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)

    club = trim(Image.open(src / "jbl-club-64c.webp").convert("RGBA"))
    gx = trim(Image.open(src / "jbl-gx9638-3.webp").convert("RGBA"))
    inf = trim(remove_white_bg(Image.open(src / "Infinity-Reference-6530cx.webp")))
    sub = trim(Image.open(src / "JBL_Stage_122.webp").convert("RGBA"))

    total = 6
    slides = [
        cover_slide(total, (sub, gx, club, inf)),
        product_slide(2, total, club, "کامپوننت 16 سانت 2Way", "JBL", "Club 64C",
                      [("توان نامی", "70W"), ("حساسیت", "92dB"), ("امپدانس", "3 Ohm")]),
        product_slide(3, total, gx, "باند بیضی 6×9 سه راهه (3Way)", "JBL", "GX9638",
                      [("توان نامی", "100W"), ("حساسیت", "94dB"), ("پاسخ فرکانسی", "45Hz")]),
        product_slide(4, total, inf, "کامپوننت 16 سانت 2Way", "Infinity", "Reference 6530CX",
                      [("توان نامی", "90W"), ("حساسیت", "93dB"), ("امپدانس", "3 Ohm")]),
        product_slide(5, total, sub, "ساب ووفر 12 اینچ", "JBL", "Stage 122",
                      [("توان نامی", "250W"), ("حداکثر توان", "1000W"), ("پاسخ فرکانسی", "34Hz")]),
        final_slide(total, 6),
    ]
    for i, s in enumerate(slides, 1):
        s.convert("RGB").save(out / f"lalehstore-post-{i:02d}.jpg", quality=93, subsampling=0)

    # contact sheet for review
    th = [s.convert("RGB").resize((360, 450), Image.LANCZOS) for s in slides]
    sheet = Image.new("RGB", (360 * 3 + 40, 450 * 2 + 30), (120, 120, 120))
    for i, t in enumerate(th):
        sheet.paste(t, (10 + (i % 3) * 370, 10 + (i // 3) * 460))
    sheet.save(out / "_sheet.png")
    print("done")


if __name__ == "__main__":
    main()
