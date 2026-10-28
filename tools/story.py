"""lalehstore daily story (1080x1920 JPG) in the light brand style.

Spec JSON:
{
  "img": "product.webp",            # product photo (white background is removed)
  "tag": "محصول روز",               # gradient pill on top
  "kind": "میکروفون یقه ای بی سیم",  # category line (Persian)
  "brand": "BOYA",                   # Latin or Persian
  "model": "Omic U",                 # model name (Latin or Persian)
  "specs": [["برد بی سیم", "50m"], ["شارژ با کیس", "15h"], ["شارژ دهی", "5h"]],
  "warranty": "24 ماه گارانتی بویا ایران",
  "cta": "استعلام قیمت در دایرکت"
}

Usage:  python3 -I story.py spec.json out.jpg
"""
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_post as mp  # noqa: E402
import make_reel as mr  # noqa: E402

mp.FONT_DIR = str(HERE / "fonts")
mp.LATIN_FONT = str(HERE / "fonts" / "quicksand-latin-700-normal.woff")
INK, CARD = mp.INK, mp.CARD


def has_fa(s):
    return any("؀" <= ch <= "ۿ" for ch in s)


def story(spec, base: Path):
    W = 1080
    img = mp.trim(mp.remove_white_bg(Image.open(base / spec["img"])))
    bg, glow = mr.make_background()
    c = bg.copy()
    c.alpha_composite(glow)
    logo = mp.brand_lockup(64)
    c.alpha_composite(logo, ((W - logo.width) // 2, 230))
    tg = mr.gradient_pill(spec.get("tag", "محصول روز"), "Black", 34)
    c.alpha_composite(tg, ((W - tg.width) // 2, 360))
    k = mp.text_img(spec["kind"], "Bold", 50, INK)
    k = mp.fit(k, W - 120, 200) if k.width > W - 120 else k
    c.alpha_composite(k, ((W - k.width) // 2, 480))
    if spec.get("brand"):
        b = mp.gradient_text(spec["brand"], "Black", 42, rtl=has_fa(spec["brand"]))
        c.alpha_composite(b, ((W - b.width) // 2, 560))
    model = spec["model"]
    m = mp.text_img(model, "Black", 96 if len(model) <= 12 else 78, INK, rtl=has_fa(model))
    m = mp.fit(m, W - 120, 200) if m.width > W - 120 else m
    c.alpha_composite(m, ((W - m.width) // 2, 622))
    sp = mr.spotlight(940, 600)
    c.alpha_composite(sp, ((W - sp.width) // 2, 1060 - sp.height // 2))
    p = mr.with_shadow(mp.fit(img, 860, 500), blur=30, opacity=75)
    c.alpha_composite(p, ((W - p.width) // 2, 1060 - p.height // 2))
    cw = (W - 128 - 2 * 22) // 3
    x = W - 64 - cw
    for label, value in spec["specs"][:3]:
        ch = mr.with_shadow(mp.chip(label, value, cw), blur=18, opacity=30, offset=(0, 8))
        pad = (ch.width - cw) // 2
        c.alpha_composite(ch, (x - pad, 1380 - pad + 8))
        x -= cw + 22
    w = mr.pill(spec["warranty"], "Bold", 32, INK, CARD)
    c.alpha_composite(w, ((W - w.width) // 2, 1585))
    ct = mr.gradient_pill(spec.get("cta", "استعلام قیمت در دایرکت"), "Black", 38)
    c.alpha_composite(ct, ((W - ct.width) // 2, 1680))
    return c.convert("RGB")


def main():
    spec_path, out = Path(sys.argv[1]), sys.argv[2]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    story(spec, spec_path.parent).save(out, quality=93, subsampling=0)
    print("story ok")


if __name__ == "__main__":
    main()
