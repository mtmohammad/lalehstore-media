"""lalehstore CREATIVE story renderer (2026-11-15, after Mohammad: «طرح خلاقانه تری نداری»).

Three bold story concepts, 1080x1920, Laleh colours (pink #EC5581 -> violet #9B6FE0 -> blue #3E95F7),
each tied to the day's reel:

  "poster" — full-bleed brand gradient, giant outlined number behind a big tilted product,
             Lalezar display headline, diagonal ticker tape, rotated spec stickers.
  "versus" — the reel's two products as a fighting-game VS card: diagonal pink/blue split,
             lightning VS badge, side-by-side stat rows (winner highlighted), poll-sticker slot.
  "night"  — dark night-drive dashboard: neon glow, big gauge whose needle points at the key
             number, glass spec cards, product glowing on a reflective floor.

Spec JSON:
{
 "style": "poster" | "versus" | "night",
 "tag": "از ریل امشب",
 "headline": "بلندتر با وات کمتر",          # short, Persian, max ~4 words
 "sub": "باند بیضی 6 در 9 سه راهه",
 "products": [ {"img": "a.png", "brand": "اینفینیتی", "model": "Primus 693M",
                "crop": [x0,y0,x1,y1] (optional)}, {...second, versus only} ],
 "big": {"v": "93dB", "k": "حساسیت"},       # poster/night: the key number
 "gauge": {"min": 80, "max": 100, "val": 93, "unit": "dB"},   # night only
 "specs": [{"k": "توان RMS", "v": "60W"}, ...],             # poster 3-4, night 4
 "rows": [{"k": "حساسیت", "a": "93dB", "b": "90dB", "win": "a"}, ...],   # versus 4
 "ticker": "INFINITY • PRIMUS 693M • 6×9 3WAY",              # poster only (Latin)
 "question": "تو کدومو برمیداری؟",                            # versus: text above the poll-sticker slot
 "warranty": "12 ماه ضمانت صوت ایران کیش",
 "cta": "استعلام قیمت در دایرکت"
}
Facts ONLY from the store's product pages. No prices.
Usage: python3 -I creative.py spec.json out.jpg
"""
import html
import json
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_post as mp  # noqa: E402

mp.FONT_DIR = str(HERE / "fonts")
mp.LATIN_FONT = str(HERE / "fonts" / "quicksand-latin-700-normal.woff")
F = (HERE / "fonts").as_uri()
FA = re.compile(r"[؀-ۿ]")


def t(s):
    s = html.escape(str(s))
    if not FA.search(s):
        return f'<span class="num">{s}</span>'
    return re.sub(r"([A-Za-z0-9][A-Za-z0-9.+/×x\-–:%]*(?:\s[A-Za-z0-9][A-Za-z0-9.+/×x\-–:%]*)*)",
                  r'<span class="lat">\1</span>', s)


CSS = f"""
@font-face{{font-family:V;src:url({F}/Vazirmatn-Black.ttf);font-weight:900}}
@font-face{{font-family:V;src:url({F}/Vazirmatn-Bold.ttf);font-weight:700}}
@font-face{{font-family:V;src:url({F}/Vazirmatn-Medium.ttf);font-weight:500}}
@font-face{{font-family:L;src:url({F}/lalezar-arabic-400-normal.woff)}}
@font-face{{font-family:M;src:url({F}/Michroma.woff2)}}
@font-face{{font-family:Q;src:url({F}/quicksand-latin-700-normal.woff)}}
:root{{--pink:#EC5581;--blue:#3E95F7;--vio:#9B6FE0;--ink:#1C1E2A;--navy:#14122b;
--grad:linear-gradient(90deg,#EC5581,#9B6FE0,#3E95F7)}}
*{{margin:0;box-sizing:border-box}} html,body{{overflow:hidden}}
body{{width:1080px;height:1920px;font-family:V;color:var(--ink)}}
#c{{position:absolute;inset:0;overflow:hidden}}
.lat{{direction:ltr;unicode-bidi:isolate}}
.num{{font-family:M;direction:ltr;unicode-bidi:isolate;letter-spacing:-1px}}
.gt{{background:var(--grad);-webkit-background-clip:text;color:transparent}}
.abs{{position:absolute}}
.grain{{position:absolute;inset:0;opacity:.18;mix-blend-mode:overlay;
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
.logo{{background:#fff;border-radius:50px;padding:14px 26px;box-shadow:0 10px 30px rgba(20,18,43,.25)}}
.logo img{{height:46px;display:block}}
.cta{{background:#fff;color:var(--ink);font-weight:900;font-size:30px;border-radius:60px;padding:16px 36px;box-shadow:0 14px 34px rgba(20,18,43,.3)}}
.cta b{{background:var(--grad);-webkit-background-clip:text;color:transparent}}
"""


def logo_bar(top, dark=False):
    return (f'<div class="abs" style="top:{top}px;left:0;right:0;display:flex;justify-content:center">'
            f'<div class="logo"><img src="logo.png"></div></div>')


# ---------------------------------------------------------------- poster
def poster(sp, P):
    big = sp["big"]
    specs = sp["specs"]
    tick = (html.escape(sp.get("ticker", "")) + " ✦ ") * 6
    stick = ""
    pos = [(60, 1440, -6, "#fff", "var(--ink)"), (750, 1430, 5, "var(--ink)", "#fff"),
           (300, 1500, 3, "#FFE45C", "var(--ink)"), (540, 1570, -4, "#fff", "var(--ink)")]
    for s, (x, y, r, bg, fg) in zip(specs, pos):
        stick += (f'<div class="abs" style="left:{x}px;top:{y}px;transform:rotate({r}deg);background:{bg};color:{fg};'
                  f'border-radius:26px;padding:18px 30px;box-shadow:0 16px 30px rgba(20,18,43,.28);text-align:center;min-width:260px">'
                  f'<div style="font-family:M;font-size:52px;line-height:1.1">{html.escape(s["v"])}</div>'
                  f'<div style="font-weight:700;font-size:28px;opacity:.8">{t(s["k"])}</div></div>')
    p = P[0]
    return f"""
<div class="abs" style="inset:0;background:linear-gradient(160deg,#EC5581 0%,#B062C9 45%,#3E95F7 100%)"></div>
<div class="abs" style="width:900px;height:900px;border-radius:50%;left:-260px;top:-260px;background:radial-gradient(circle,rgba(255,255,255,.35),transparent 65%)"></div>
<div class="abs" style="width:1000px;height:1000px;border-radius:50%;right:-420px;bottom:-200px;background:radial-gradient(circle,rgba(20,18,43,.35),transparent 65%)"></div>
<div class="grain"></div>
{logo_bar(150)}
<div class="abs" style="top:290px;left:0;right:0;text-align:center;color:#fff">
  <span style="display:inline-block;border:3px solid #fff;border-radius:40px;padding:6px 26px;font-weight:700;font-size:30px">{t(sp.get("tag", ""))}</span>
  <div style="font-family:L;font-size:150px;line-height:1.05;margin-top:18px;text-shadow:0 10px 30px rgba(20,18,43,.3)">{t(sp["headline"])}</div>
  <div style="font-weight:700;font-size:38px;opacity:.95;margin-top:6px">{t(sp["sub"])}</div>
</div>
<div class="abs" style="top:640px;left:0;right:0;text-align:center;font-family:M;font-size:250px;line-height:1;
  color:transparent;-webkit-text-stroke:5px rgba(255,255,255,.75);letter-spacing:-6px;direction:ltr">{html.escape(big["v"])}</div>
<div class="abs" style="top:600px;left:0;right:0;text-align:center"><span style="background:var(--ink);color:#fff;font-weight:900;font-size:32px;padding:6px 26px;border-radius:14px">{t(big["k"])}</span></div>
<img src="{p}" class="abs" style="left:250px;top:760px;width:580px;transform:rotate(-8deg);filter:drop-shadow(0 50px 50px rgba(20,18,43,.45))">
<div class="abs" style="top:1345px;left:-60px;width:1200px;transform:rotate(-5deg);background:var(--ink);color:#fff;padding:14px 0;white-space:nowrap;overflow:hidden;font-family:M;font-size:30px;direction:ltr;letter-spacing:2px">{tick}</div>
{stick}
<div class="abs" style="top:1720px;left:0;right:0;display:flex;justify-content:center;gap:18px;align-items:center">
  <span class="cta"><b>{t(sp.get("cta", "استعلام قیمت در دایرکت"))}</b></span>
  <span style="color:#fff;font-weight:700;font-size:26px">✅ {t(sp["warranty"])}</span></div>
"""


# ---------------------------------------------------------------- versus
def versus(sp, P):
    a, b = sp["products"][0], sp["products"][1]
    rows = ""
    for r in sp["rows"]:
        wa = r.get("win") == "a"
        wb = r.get("win") == "b"
        cell = ('flex:1;text-align:center;font-family:M;font-size:44px;padding:10px 0;border-radius:20px;')
        rows += (f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px">'
                 f'<div style="{cell}{"background:#fff;color:var(--pink);box-shadow:0 10px 24px rgba(236,85,129,.35)" if wa else "color:#fff"}">{html.escape(r["a"])}</div>'
                 f'<div style="width:230px;text-align:center;font-weight:900;font-size:30px;color:#fff;background:rgba(20,18,43,.55);border-radius:16px;padding:12px 0">{t(r["k"])}</div>'
                 f'<div style="{cell}{"background:#fff;color:var(--blue);box-shadow:0 10px 24px rgba(62,149,247,.35)" if wb else "color:#fff"}">{html.escape(r["b"])}</div></div>')
    return f"""
<div class="abs" style="inset:0;background:#3E95F7"></div>
<div class="abs" style="inset:0;background:linear-gradient(160deg,#ff6f98,#EC5581);clip-path:polygon(0 0,100% 0,100% 30%,0 58%)"></div>
<div class="abs" style="inset:0;background:linear-gradient(200deg,#5aa8ff,#3E7BF7);clip-path:polygon(0 58%,100% 30%,100% 100%,0 100%)"></div>
<div class="abs" style="left:-100px;right:-100px;top:780px;height:16px;background:#fff;transform:rotate(-14.5deg);box-shadow:0 0 40px #fff"></div>
<div class="grain"></div>
{logo_bar(140)}
<div class="abs" style="top:250px;right:60px;color:#fff;text-align:right">
  <div style="font-weight:700;font-size:30px;opacity:.9">{t(sp.get("tag", ""))}</div>
  <div style="font-family:L;font-size:96px;line-height:1.05">{t(a["brand"])}</div>
  <div style="font-family:M;font-size:42px">{html.escape(a["model"])}</div></div>
<img src="{P[0]}" class="abs" style="left:40px;top:250px;width:520px;transform:rotate(-10deg);filter:drop-shadow(0 30px 30px rgba(20,18,43,.4))">
<div class="abs" style="left:400px;top:600px;width:280px;height:280px;display:flex;align-items:center;justify-content:center">
  <svg width="280" height="280" viewBox="0 0 300 300" style="position:absolute"><polygon points="150,8 185,105 290,110 205,170 240,280 150,215 60,280 95,170 10,110 115,105" fill="#FFE45C" stroke="#1C1E2A" stroke-width="10" stroke-linejoin="round"/></svg>
  <span style="position:relative;font-family:M;font-size:84px;color:var(--ink);font-style:italic;letter-spacing:-4px">VS</span></div>
<img src="{P[1]}" class="abs" style="right:50px;top:930px;width:500px;transform:rotate(6deg);filter:drop-shadow(0 30px 30px rgba(20,18,43,.4))">
<div class="abs" style="top:900px;left:60px;color:#fff;text-align:left;direction:ltr">
  <div style="font-family:L;font-size:96px;line-height:1.05;direction:rtl;text-align:left">{t(b["brand"])}</div>
  <div style="font-family:M;font-size:42px">{html.escape(b["model"])}</div></div>
<div class="abs" style="top:1150px;left:50px;right:50px">
  <div style="display:flex;gap:14px;margin-bottom:10px;color:#fff;font-weight:900;font-size:26px;text-align:center">
    <div style="flex:1">{t(a["brand"])}</div><div style="width:230px"></div><div style="flex:1">{t(b["brand"])}</div></div>
  {rows}</div>
<div class="abs" style="top:1560px;left:0;right:0;text-align:center">
  <div style="font-family:L;font-size:70px;color:#fff;text-shadow:0 6px 20px rgba(20,18,43,.35)">{t(sp.get("question", "تو کدومو برمیداری؟"))}</div>
  <div style="margin:8px auto 0;width:560px;height:110px;border:4px dashed rgba(255,255,255,.8);border-radius:26px;color:rgba(255,255,255,.85);font-weight:700;font-size:26px;display:flex;align-items:center;justify-content:center">جای استیکر نظرسنجی</div></div>
<div class="abs" style="top:1810px;left:0;right:0;text-align:center;color:#fff;font-weight:700;font-size:26px">{t(sp.get("cta", "استعلام قیمت در دایرکت"))} · lalehstore.com</div>
"""


# ---------------------------------------------------------------- night
def night(sp, P):
    g = sp["gauge"]
    lo, hi, val = g["min"], g["max"], g["val"]
    import math
    cx, cy, R = 540, 760, 300
    ticks = ""
    n = hi - lo
    for i in range(n + 1):
        ang = math.radians(180 + 180 * i / n)
        r1 = R - (34 if i % 5 == 0 else 18)
        x1, y1 = cx + R * math.cos(ang), cy + R * math.sin(ang)
        x2, y2 = cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)
        hot = lo + i >= val
        ticks += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{"#EC5581" if hot else "#7fb6ff"}" '
                  f'stroke-width="{6 if i % 5 == 0 else 3}" stroke-linecap="round"/>')
        if i % 5 == 0:
            xl, yl = cx + (R - 80) * math.cos(ang), cy + (R - 80) * math.sin(ang)
            ticks += f'<text x="{xl:.1f}" y="{yl + 10:.1f}" fill="#c9d3ff" font-family="M" font-size="28" text-anchor="middle">{lo + i}</text>'
    na = math.radians(180 + 180 * (val - lo) / n)
    nx, ny = cx + (R - 50) * math.cos(na), cy + (R - 50) * math.sin(na)
    frac = (val - lo) / n
    arc_len = math.pi * (R + 26)
    cards = ""
    for s in sp["specs"][:4]:
        cards += (f'<div style="flex:1;background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.18);border-radius:26px;padding:18px 8px;text-align:center;backdrop-filter:blur(6px)">'
                  f'<div style="font-family:M;font-size:40px;color:#fff">{html.escape(s["v"])}</div>'
                  f'<div style="font-weight:700;font-size:24px;color:#c9d3ff;margin-top:4px">{t(s["k"])}</div></div>')
    p = P[0]
    return f"""
<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 30%,#2a2160 0%,#14122b 55%,#0b0a1a 100%)"></div>
<div class="abs" style="width:700px;height:700px;left:-250px;top:900px;border-radius:50%;background:radial-gradient(circle,rgba(236,85,129,.45),transparent 65%)"></div>
<div class="abs" style="width:700px;height:700px;right:-250px;top:700px;border-radius:50%;background:radial-gradient(circle,rgba(62,149,247,.45),transparent 65%)"></div>
<div class="abs" style="inset:0;background-image:radial-gradient(rgba(255,255,255,.5) 1.5px,transparent 2px);background-size:90px 110px;opacity:.25"></div>
{logo_bar(130)}
<div class="abs" style="top:240px;left:0;right:0;text-align:center;color:#fff">
  <span style="font-weight:700;font-size:28px;color:#ff8fb0;letter-spacing:1px">{t(sp.get("tag", ""))}</span>
  <div style="font-family:L;font-size:96px;line-height:1.1;text-shadow:0 0 30px rgba(236,85,129,.8)">{t(sp["headline"])}</div></div>
<svg class="abs" style="left:0;top:0" width="1080" height="1000" viewBox="0 0 1080 1000">
  <defs><linearGradient id="ng" x1="0" x2="1"><stop offset="0" stop-color="#3E95F7"/><stop offset=".6" stop-color="#9B6FE0"/><stop offset="1" stop-color="#EC5581"/></linearGradient>
  <filter id="gl"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <path d="M {cx - R - 26} {cy} A {R + 26} {R + 26} 0 0 1 {cx + R + 26} {cy}" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="18" stroke-linecap="round"/>
  <path d="M {cx - R - 26} {cy} A {R + 26} {R + 26} 0 0 1 {cx + R + 26} {cy}" fill="none" stroke="url(#ng)" stroke-width="18" stroke-linecap="round"
        stroke-dasharray="{arc_len * frac:.1f} 9999" filter="url(#gl)"/>
  {ticks}
  <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#EC5581" stroke-width="10" stroke-linecap="round" filter="url(#gl)"/>
  <circle cx="{cx}" cy="{cy}" r="26" fill="#fff"/><circle cx="{cx}" cy="{cy}" r="12" fill="#EC5581"/>
</svg>
<div class="abs" style="top:790px;left:0;right:0;text-align:center;color:#fff">
  <div style="font-family:M;font-size:110px;line-height:1;text-shadow:0 0 30px rgba(62,149,247,.9)">{html.escape(sp["big"]["v"])}</div>
  <div style="font-weight:700;font-size:34px;color:#c9d3ff">{t(sp["big"]["k"])}</div></div>
<div class="abs" style="top:985px;left:0;right:0;text-align:center;color:#fff">
  <div style="font-weight:900;font-size:50px">{t(p_brand(sp))}</div>
  <div style="font-weight:500;font-size:30px;color:#c9d3ff">{t(sp["sub"])}</div></div>
<div class="abs" style="left:240px;top:1470px;width:600px;height:60px;border-radius:50%;background:radial-gradient(ellipse,rgba(155,111,224,.7),transparent 70%)"></div>
<img src="{p}" class="abs" style="left:330px;top:1105px;width:420px;filter:drop-shadow(0 0 40px rgba(155,111,224,.7))">
<div class="abs" style="top:1560px;left:50px;right:50px;display:flex;gap:16px;direction:rtl">{cards}</div>
<div class="abs" style="top:1705px;left:0;right:0;text-align:center;color:#c9d3ff;font-weight:700;font-size:28px">✅ {t(sp["warranty"])}</div>
<div class="abs" style="top:1760px;left:0;right:0;display:flex;justify-content:center"><span class="cta" style="padding:12px 34px"><b>{t(sp.get("cta", "استعلام قیمت در دایرکت"))}</b></span></div>
"""


def p_brand(sp):
    p = sp["products"][0]
    return f'{p["brand"]} {p["model"]}'


def render(spec_path, out_path):
    spec_path = Path(spec_path).resolve()
    base = spec_path.parent
    sp = json.loads(spec_path.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="creative_"))
    names = []
    for i, p in enumerate(sp["products"]):
        im = Image.open(base / p["img"]).convert("RGBA")
        if p.get("crop"):
            im = im.crop(tuple(p["crop"]))
        if im.getextrema()[3][0] == 255:
            im = mp.remove_white_bg(im)
        im = mp.trim(im)
        im.save(tmp / f"p{i}.png")
        names.append(f"p{i}.png")
    mp.brand_lockup(120).save(tmp / "logo.png")
    body = {"poster": poster, "versus": versus, "night": night}[sp["style"]](sp, names)
    (tmp / "s.html").write_text(f'<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>{CSS}</style></head>'
                                f'<body><div id="c">{body}</div></body></html>')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        pg.goto((tmp / "s.html").as_uri())
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(tmp / "big.png"))
        b.close()
    Image.open(tmp / "big.png").convert("RGB").resize((1080, 1920), Image.LANCZOS).save(out_path, quality=93)
    print("creative ok", out_path)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
