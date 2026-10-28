"""Build WhatsApp profile images for lalehstore.

The mark is redrawn as clean vector geometry (traced from the site logo),
the wordmark is set in Quicksand Bold and the Persian line in Vazirmatn.

Usage:
  python3 -I make_wa.py <quicksand_bold.woff> <vazirmatn_bold.ttf> <out_dir>
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

PINK = (236, 85, 129)
BLUE = (62, 149, 247)
NAVY = (55, 50, 123)
DARK = (40, 42, 54)

SIZE = 1080
SS = 4  # supersampling for smooth edges

# ---------------------------------------------------------------------------
# Mark geometry (units traced from the logo; pink piece, clockwise in image
# coordinates). The blue piece is the same shape rotated 180 degrees.
# Each vertex: (x, y, corner_radius)
# ---------------------------------------------------------------------------
PINK_SHAPE = [
    (345, 280, 60),   # top-left (curves straight into the tip)
    (412, 280, 3),    # sharp tip
    (735, 603, 55),   # end of the diagonal edge
    (735, 690, 55),   # bottom-right
    (345, 690, 55),   # bottom-left
]
ROT_CENTER = (570, 535)
MARK_BOX = (345, 280, 795, 790)  # x0, y0, x1, y1 of both pieces together


def fillet(verts, steps=24):
    """Return a polygon point list with each corner rounded by its own radius."""
    pts = []
    n = len(verts)
    for i in range(n):
        px, py, _ = verts[i - 1]
        cx, cy, r = verts[i]
        nx, ny, _ = verts[(i + 1) % n]
        v1 = (px - cx, py - cy)
        v2 = (nx - cx, ny - cy)
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        cos_t = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        theta = math.acos(cos_t)
        if r <= 0 or theta < 1e-6:
            pts.append((cx, cy))
            continue
        t = r / math.tan(theta / 2)
        t1 = (cx + u1[0] * t, cy + u1[1] * t)
        t2 = (cx + u2[0] * t, cy + u2[1] * t)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        d = r / math.sin(theta / 2)
        oc = (cx + bis[0] / bl * d, cy + bis[1] / bl * d)
        a1 = math.atan2(t1[1] - oc[1], t1[0] - oc[0])
        a2 = math.atan2(t2[1] - oc[1], t2[0] - oc[0])
        da = a2 - a1
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(steps + 1):
            a = a1 + da * k / steps
            pts.append((oc[0] + r * math.cos(a), oc[1] + r * math.sin(a)))
    return pts


def render_mark(width: int) -> Image.Image:
    """Render the two-piece mark as an RGBA image `width` pixels wide."""
    x0, y0, x1, y1 = MARK_BOX
    scale = width * SS / (x1 - x0)
    w, h = round((x1 - x0) * scale), round((y1 - y0) * scale)

    pink_pts = fillet(PINK_SHAPE)
    cx, cy = ROT_CENTER
    blue_pts = [(2 * cx - x, 2 * cy - y) for x, y in pink_pts]

    def mask(points):
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).polygon([((x - x0) * scale, (y - y0) * scale) for x, y in points], fill=255)
        return m

    pm, bm = mask(pink_pts), mask(blue_pts)
    nm = ImageChops.multiply(pm, bm)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(PINK + (255,), (0, 0), pm)
    out.paste(BLUE + (255,), (0, 0), bm)
    out.paste(NAVY + (255,), (0, 0), nm)
    return out.convert("RGBa").resize((width, round(h / SS)), Image.LANCZOS).convert("RGBA")


def render_wordmark(font_path: str, width: int) -> Image.Image:
    """'laleh' in pink + 'store' in blue, letter-spaced, scaled to `width`."""
    size = 200 * SS
    font = ImageFont.truetype(font_path, size)
    tracking = size * 0.09
    parts = [(ch, PINK) for ch in "laleh"] + [(ch, BLUE) for ch in "store"]
    total = sum(font.getlength(ch) for ch, _ in parts) + tracking * (len(parts) - 1)
    canvas = Image.new("RGBA", (int(total + size), int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    x = size / 2
    for ch, col in parts:
        d.text((x, size * 0.2), ch, font=font, fill=col + (255,),
               stroke_width=round(size * 0.012), stroke_fill=col + (255,))
        x += font.getlength(ch) + tracking
    canvas = canvas.crop(canvas.getchannel("A").getbbox())
    h = round(canvas.height * width / canvas.width)
    return canvas.convert("RGBa").resize((width, h), Image.LANCZOS).convert("RGBA")


def render_fa(font_path: str, text: str, px: int) -> Image.Image:
    font = ImageFont.truetype(font_path, px * SS, layout_engine=ImageFont.Layout.RAQM)
    layer = Image.new("RGBA", (SIZE * SS, px * SS * 3), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (layer.width // 2, layer.height // 2), text, font=font,
        fill=DARK + (255,), anchor="mm", direction="rtl",
    )
    layer = layer.crop(layer.getchannel("A").getbbox())
    return layer.convert("RGBa").resize((layer.width // SS, layer.height // SS), Image.LANCZOS).convert("RGBA")


def soft_background() -> Image.Image:
    """White with very faint pink and blue glows in opposite corners."""
    bg = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((-300, -300, 520, 520), fill=PINK + (36,))
    g.ellipse((560, 560, 1380, 1380), fill=BLUE + (36,))
    bg.alpha_composite(glow.convert("RGBa").filter(ImageFilter.GaussianBlur(170)).convert("RGBA"))
    return bg


def circle_preview(img: Image.Image) -> Image.Image:
    """How WhatsApp will crop the avatar (circle on grey)."""
    bg = Image.new("RGBA", img.size, (225, 225, 225, 255))
    m = Image.new("L", (img.width * 4, img.height * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, m.width - 1, m.height - 1), fill=255)
    bg.paste(img, (0, 0), m.resize(img.size, Image.LANCZOS))
    return bg


def stack(canvas: Image.Image, items, gaps) -> None:
    total = sum(i.height for i in items) + sum(gaps)
    y = (canvas.height - total) // 2
    for idx, im in enumerate(items):
        canvas.alpha_composite(im, ((canvas.width - im.width) // 2, y))
        y += im.height + (gaps[idx] if idx < len(gaps) else 0)


def main() -> None:
    latin_font, fa_font, out_dir = sys.argv[1:4]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Variant 1: full logo (mark + wordmark + Persian line)
    v1 = soft_background()
    stack(
        v1,
        [render_mark(300), render_wordmark(latin_font, 720)],
        [70],
    )
    v1.convert("RGB").save(out / "lalehstore-whatsapp-profile.png", optimize=True)
    circle_preview(v1).save(out / "preview-profile.png")

    # Variant 2: mark only (reads best at tiny avatar sizes)
    v2 = soft_background()
    stack(v2, [render_mark(500)], [])
    v2.convert("RGB").save(out / "lalehstore-whatsapp-icon.png", optimize=True)
    circle_preview(v2).save(out / "preview-icon.png")

    print("done")


if __name__ == "__main__":
    main()
