"""lalehstore INFO-STORY renderer (since 2026-11-13, Mohammad's pick): daily story as a
product infographic, 1080x1920, Laleh colours (light pink/blue background, pink->violet->blue
gradient, white cards, Vazirmatn). Two styles, alternate them day by day:

  "callout" — product in the centre on rings, 6 spec cards around it joined to the product
              with gradient leader lines (the BOYA Magic-05 look).
  "hud"     — one cinematic scene (the Pioneer 7002 look): title top-right, a HUD row
              (gradient label bar + [main value] + pulse line + gauge), a hologram bar chart of
              5 values (last one pink and underlined), the product on a perspective grid floor
              with rings, 3-4 spec chips.

Both carry extra graphic elements: dotted patterns, sparkles, rings, floating gradient
orbs, plus marks, a wave ribbon, numbered badges.

Spec JSON (all text Persian unless it is a spec value; Latin runs are isolated automatically):
{
  "style": "callout",                    # or "hud"
  "img": "product.png",                  # store photo (from data-large_image)
  "crop": [x0, y0, x1, y1],              # optional: crop away the «Laleh Store» watermark / empty space
  "keep_bg": false,                      # true = keep white bg and blend (use for white parts e.g. antennas)
  "tag": "محصول روز",
  "kind": "میکروفون یقه ای دو کاربره",     # category line
  "brand": "بویا", "brand_en": "BOYA", "model": "Magic-05",
  "specs": [                             # callout only: exactly 6
     {"k": "برد بی سیم", "v": "100m", "s": "بدون مانع", "icon": "signal"}
  ],
  "hero": {"k": "توان در 4 اهم", "v": "2×70W"},          # hud only
  "bars": [{"v": "15Hz", "k": "پاسخ از"}, ... 5 items],   # hud only; 5th is highlighted
  "chips": ["کلاس AB", "فیوز 40A", ...],                  # hud only: 3-4 short items
  "warranty": "24 ماه گارانتی بویا ایران",  # exactly as on the product page
  "cta": "استعلام قیمت در دایرکت"
}
Icons: any name in tools/icons (signal, battery, mic, speaker, bolt, plug, wifi, magnet, gear, ...).
Facts ONLY from the store's product page (H1, table.shop_attributes, description). No prices.

Usage:  python3 -I infostory.py spec.json out.jpg
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
ICONS = (HERE / "icons").as_uri()
FA = re.compile(r"[؀-ۿ]")


def t(s):
    """Escape and isolate Latin/number runs inside Persian text."""
    s = html.escape(str(s))
    if not FA.search(s):
        return f'<span class="num">{s}</span>'
    return re.sub(r"([A-Za-z0-9][A-Za-z0-9.+/×x\-–:%]*(?:\s[A-Za-z0-9][A-Za-z0-9.+/×x\-–:%]*)*)",
                  r'<span class="lat">\1</span>', s)


CSS = f"""
@font-face{{font-family:V;src:url({F}/Vazirmatn-Black.ttf);font-weight:900}}
@font-face{{font-family:V;src:url({F}/Vazirmatn-Bold.ttf);font-weight:700}}
@font-face{{font-family:V;src:url({F}/Vazirmatn-Medium.ttf);font-weight:500}}
@font-face{{font-family:M;src:url({F}/Michroma.woff2)}}
:root{{--pink:#EC5581;--blue:#3E95F7;--vio:#9B6FE0;--ink:#1C1E2A;--mut:#6b6f80;--grad:linear-gradient(90deg,#EC5581,#9B6FE0,#3E95F7)}}
*{{margin:0;box-sizing:border-box}} html,body{{overflow:hidden}}
body{{width:1080px;height:1920px;font-family:V;color:var(--ink)}}
#c{{position:absolute;inset:0;width:1080px;height:1920px;overflow:hidden;
background:radial-gradient(ellipse at 6% 10%,rgba(236,85,129,.30),transparent 38%),radial-gradient(ellipse at 98% 42%,rgba(62,149,247,.26),transparent 40%),radial-gradient(ellipse at 30% 92%,rgba(155,111,224,.20),transparent 45%),#f7f3f9}}
.lat{{direction:ltr;unicode-bidi:isolate}}
.num{{font-family:M;direction:ltr;unicode-bidi:isolate}}
.gt{{background:var(--grad);-webkit-background-clip:text;color:transparent}}
.card{{background:#fff;border-radius:30px;box-shadow:0 14px 34px rgba(40,30,80,.10);position:relative}}
.card:after{{content:"";position:absolute;inset:0;border-radius:30px;border:2px solid rgba(155,111,224,.14);pointer-events:none}}
.pill{{display:inline-block;background:var(--grad);color:#fff;font-weight:700;font-size:28px;border-radius:40px;padding:8px 28px;box-shadow:0 10px 24px rgba(236,85,129,.3)}}
.dots{{position:absolute;background-image:radial-gradient(rgba(155,111,224,.45) 3px,transparent 3.5px);background-size:30px 30px}}
.orb{{position:absolute;border-radius:50%;background:var(--grad);opacity:.9;box-shadow:0 14px 30px rgba(155,111,224,.35)}}
.orb.o{{background:none;border:4px solid rgba(62,149,247,.35);box-shadow:none}}
.plus{{position:absolute;font-family:M;font-size:44px;color:rgba(236,85,129,.55)}}
.spark{{position:absolute}}
.foot{{position:absolute;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:18px;background:#fff;border-radius:60px;padding:10px 12px 10px 28px;box-shadow:0 12px 34px rgba(40,30,80,.18);white-space:nowrap}}
.foot img{{height:44px}} .cta{{background:var(--grad);color:#fff;font-weight:900;font-size:27px;border-radius:40px;padding:10px 26px}}
.badge{{width:66px;height:66px;border-radius:20px;background:linear-gradient(135deg,#ffe3ec,#e3eeff);display:flex;align-items:center;justify-content:center;flex:none}}
.badge img{{width:50px;height:50px}}
.no{{font-family:M;font-size:18px;color:rgba(155,111,224,.7)}}
"""

SPARK = ('<svg class="spark" style="{pos}" width="{s}" height="{s}" viewBox="0 0 40 40"><path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 '
         'C18 26 14 22 0 20 C14 18 18 14 20 0Z" fill="url(#sg)"/></svg>')
DEFS = ('<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="sg" x1="0" x2="1" y1="0" y2="1">'
        '<stop offset="0" stop-color="#EC5581"/><stop offset="1" stop-color="#3E95F7"/></linearGradient>'
        '<linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#EC5581"/><stop offset="1" stop-color="#3E95F7"/></linearGradient></defs></svg>')
WAVE = ('<svg style="position:absolute;left:0;top:{y}px" width="1080" height="160" viewBox="0 0 1080 160">'
        '<path d="M0 90 C180 20 320 150 540 80 S900 20 1080 70" fill="none" stroke="url(#lg)" stroke-width="5" opacity=".45"/>'
        '<path d="M0 120 C200 60 360 170 560 110 S920 60 1080 100" fill="none" stroke="url(#lg)" stroke-width="2.5" opacity=".3"/></svg>')


def spark(x, y, s=40):
    return SPARK.format(pos=f"left:{x}px;top:{y}px", s=s)


def icon(name):
    return f'<div class="badge"><img src="{ICONS}/{name}.webp"></div>' if name else ""


def header(sp, top=230, align="center"):
    brand = f'{html.escape(sp.get("brand", ""))} ' if sp.get("brand") else ""
    return (f'<div style="position:absolute;top:{top}px;left:60px;right:60px;text-align:{align}">'
            f'<span class="pill">{t(sp.get("tag", "محصول روز"))}</span>'
            f'<div style="font-weight:700;font-size:34px;color:var(--mut);margin-top:22px">{t(sp["kind"])}</div>'
            f'<div style="font-weight:900;font-size:76px;line-height:1.15;margin-top:4px">{brand}<span class="lat">{html.escape(sp["model"])}</span></div></div>')


def footer(sp, top):
    return (f'<div style="position:absolute;top:{top}px;left:0;right:0;text-align:center">'
            f'<span class="card" style="display:inline-block;padding:12px 30px;font-weight:700;font-size:28px;border-radius:40px">✅ {t(sp["warranty"])}</span></div>'
            f'<div class="foot" style="top:{top + 100}px"><span class="cta">{t(sp.get("cta", "استعلام قیمت در دایرکت"))}</span><img src="logo.png"></div>')


def callout(sp, pimg):
    specs = sp["specs"]
    assert len(specs) == 6, "callout needs 6 specs"
    cy = 1010
    rows = [620, 920, 1220]
    out = [DEFS, '<div class="dots" style="left:40px;top:120px;width:240px;height:150px"></div>',
           '<div class="dots" style="right:30px;top:1560px;width:210px;height:120px"></div>',
           '<div class="orb" style="width:70px;height:70px;right:90px;top:170px"></div>',
           '<div class="orb o" style="width:150px;height:150px;left:-40px;top:1500px"></div>',
           '<div class="orb" style="width:34px;height:34px;left:120px;top:1640px;opacity:.6"></div>',
           '<div class="plus" style="right:200px;top:520px">+</div><div class="plus" style="left:200px;top:1420px">+</div>',
           WAVE.format(y=1400), header(sp)]
    for d, st in ((720, "background:radial-gradient(circle,#fff 0,rgba(255,255,255,.7) 45%,transparent 70%)"),
                  (660, "border:3px dashed rgba(155,111,224,.35)"), (520, "border:2px solid rgba(62,149,247,.25)")):
        out.append(f'<div style="position:absolute;left:50%;top:{cy}px;width:{d}px;height:{d}px;transform:translate(-50%,-50%);border-radius:50%;{st}"></div>')
    lines, dots = [], []
    for i, y in enumerate(rows):
        yc = y + 80
        for side in (0, 1):
            x0 = 744 if side == 0 else 336
            tx = 540 + (175 if side == 0 else -175) * (0.8 if i == 1 else 1)
            ty = yc + (30 if i == 0 else -30 if i == 2 else 0)
            mid = x0 + (-40 if side == 0 else 40)
            lines.append(f'<polyline points="{x0},{yc} {mid},{yc} {tx},{ty}"/>')
            dots.append(f'<div style="position:absolute;left:{tx - 11}px;top:{ty - 11}px;width:22px;height:22px;border-radius:50%;background:var(--grad);box-shadow:0 0 0 8px rgba(155,111,224,.18)"></div>')
    out.append('<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><g stroke="url(#lg)" stroke-width="3.5" fill="none">' + "".join(lines) + "</g></svg>")
    out.append(f'<img src="{pimg}" style="position:absolute;left:50%;top:{cy}px;max-width:560px;max-height:560px;transform:translate(-50%,-50%);{sp["_imgcss"]}">')
    out += dots
    out += [spark(300, cy - 330, 46), spark(720, cy + 250, 34), spark(760, cy - 280, 26)]
    for i, s in enumerate(specs):
        y = rows[i // 2]
        side = "right" if i % 2 == 0 else "left"
        v = t(s["v"])
        sub = f'<div style="font-weight:500;font-size:22px;color:var(--mut)">{t(s["s"])}</div>' if s.get("s") else ""
        out.append(f'<div class="card" style="position:absolute;{side}:36px;top:{y}px;width:300px;padding:20px 22px;text-align:right">'
                   f'<div style="display:flex;align-items:center;gap:12px;justify-content:space-between">'
                   f'<div style="font-weight:700;font-size:23px;color:var(--mut)">{t(s["k"])}</div>{icon(s.get("icon"))}</div>'
                   f'<div class="gt" style="font-weight:900;font-size:38px;line-height:1.25;margin-top:6px">{v}</div>{sub}'
                   f'<div class="no" style="position:absolute;left:18px;bottom:12px">0{i + 1}</div></div>')
    out.append(footer(sp, 1540))
    return "".join(out)


def hud(sp, pimg):
    bars, chips, hero = sp["bars"], sp["chips"], sp["hero"]
    assert len(bars) == 5 and 3 <= len(chips) <= 4, "hud needs hero, 5 bars, 3-4 chips"
    brand = f'{html.escape(sp.get("brand", ""))} ' if sp.get("brand") else ""
    out = [DEFS,
           '<div class="dots" style="left:40px;top:160px;width:250px;height:160px"></div>',
           '<div class="orb" style="width:64px;height:64px;left:330px;top:250px"></div>',
           '<div class="orb o" style="width:170px;height:170px;right:-50px;top:820px"></div>',
           '<div class="orb" style="width:28px;height:28px;left:90px;top:900px;opacity:.6"></div>',
           '<div class="plus" style="right:120px;top:1130px">+</div>',
           # perspective floor + rings
           '<div style="position:absolute;left:-30%;right:-30%;top:1080px;height:520px;transform:perspective(600px) rotateX(64deg);transform-origin:bottom;'
           'background-image:linear-gradient(rgba(62,149,247,.25) 2px,transparent 2px),linear-gradient(90deg,rgba(236,85,129,.22) 2px,transparent 2px);background-size:90px 90px;'
           '-webkit-mask-image:linear-gradient(to top,#000 30%,transparent 95%)"></div>',
           '<div style="position:absolute;left:50%;top:1270px;width:980px;height:300px;transform:translate(-50%,-50%);border-radius:50%;border:3px solid rgba(236,85,129,.5);box-shadow:0 0 20px rgba(236,85,129,.25)"></div>',
           '<div style="position:absolute;left:50%;top:1270px;width:800px;height:230px;transform:translate(-50%,-50%);border-radius:50%;border:2px solid rgba(62,149,247,.35)"></div>']
    out.append(f'<div style="position:absolute;right:60px;top:230px;text-align:right"><span class="pill">{t(sp.get("tag", "محصول روز"))}</span>'
               f'<div style="font-weight:900;font-size:72px;line-height:1.15;margin-top:20px">{t(sp["kind"])}</div>'
               f'<div style="font-weight:900;font-size:56px;margin-top:2px">{brand}<span class="lat gt">{html.escape(sp["model"])}</span></div></div>')
    # HUD row
    out.append('<div style="position:absolute;left:30px;width:340px;top:612px;height:60px;border-radius:30px;background:linear-gradient(90deg,#EC5581,#3E95F7);filter:blur(10px);opacity:.75"></div>'
               f'<div style="position:absolute;left:70px;top:614px;width:290px;font-weight:900;font-size:30px;color:#fff;text-shadow:0 2px 8px rgba(120,40,90,.5);white-space:nowrap">{t(hero["k"])}</div>'
               f'<div style="position:absolute;left:390px;top:590px;padding:6px 24px;font-family:M;font-size:50px;direction:ltr" class="gt">'
               f'<span style="position:absolute;left:0;top:0;bottom:0;width:14px;border:3px solid #9B6FE0;border-right:none"></span>{html.escape(hero["v"])}'
               '<span style="position:absolute;right:0;top:0;bottom:0;width:14px;border:3px solid #9B6FE0;border-left:none"></span></div>'
               '<svg style="position:absolute;left:0;top:0;filter:drop-shadow(0 0 6px rgba(62,149,247,.45))" width="1080" height="800">'
               '<polyline points="700,640 715,640 725,610 735,670 745,625 755,655 765,640 780,640 790,620 800,660 810,640 840,640" fill="none" stroke="#3E95F7" stroke-width="3"/>'
               '<g transform="translate(850,560) scale(0.95)"><path d="M15 115 A90 90 0 0 1 195 115" fill="none" stroke="#3E95F7" stroke-width="5"/>'
               '<path d="M150 40 A90 90 0 0 1 195 115" fill="none" stroke="#EC5581" stroke-width="7"/>'
               '<g stroke="#3E95F7" stroke-width="3"><line x1="35" y1="70" x2="45" y2="76"/><line x1="105" y1="28" x2="105" y2="40"/><line x1="70" y1="38" x2="76" y2="48"/><line x1="140" y1="38" x2="134" y2="48"/></g>'
               '<line x1="105" y1="112" x2="160" y2="55" stroke="#1C1E2A" stroke-width="5" stroke-linecap="round"/><circle cx="105" cy="112" r="9" fill="none" stroke="#1C1E2A" stroke-width="4"/></g></svg>')
    # hologram bars
    hs = [26, 60, 98, 140, 195]
    g = ['<svg style="position:absolute;left:0;top:0" width="1080" height="1920"><defs><linearGradient id="hb" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#3E95F7" stop-opacity=".45"/><stop offset="1" stop-color="#9B6FE0" stop-opacity=".08"/></linearGradient></defs>']
    base = 960
    for i, h in enumerate(hs):
        x = 140 + i * 140 - (10 if i == 4 else 0)
        w = 105 if i < 4 else 125
        yb = base + i * 6
        col = "#EC5581" if i == 4 else "#3E95F7"
        g.append(f'<rect x="{x}" y="{yb - h}" width="{w}" height="{h}" fill="url(#hb)" stroke="{col}" stroke-width="3.5" style="filter:drop-shadow(0 0 6px {col}88)"/>')
    g.append(f'<polyline points="110,{base + 85} 120,{base + 97} 870,{base + 130} 860,{base + 118}" fill="none" stroke="url(#lg)" stroke-width="2.5"/>'
             f'<line x1="520" y1="{base + 115}" x2="490" y2="{base + 215}" stroke="#9B6FE0" stroke-width="2" opacity=".7"/></svg>')
    out.append("".join(g))
    for i, bdat in enumerate(bars):
        cx = 192 + i * 140 + (8 if i == 4 else 0)
        y = base + 14 + i * 6
        last = i == 4
        st = "color:#EC5581;border-bottom:4px solid #EC5581" if last else "color:#3E95F7"
        out.append(f'<div style="position:absolute;left:{cx}px;top:{y}px;transform:translateX(-50%) skewY(3deg);font-family:M;font-size:{30 if last else 25}px;direction:ltr;white-space:nowrap;{st}">{html.escape(bdat["v"])}</div>'
                   f'<div style="position:absolute;left:{cx}px;top:{y + 56}px;transform:translateX(-50%);font-weight:700;font-size:21px;white-space:nowrap;color:{"#EC5581" if last else "#555a6c"}">{t(bdat["k"])}</div>')
    out.append(f'<img src="{pimg}" style="position:absolute;left:50%;top:1300px;max-width:700px;max-height:400px;transform:translate(-50%,-50%) rotate(-3deg);{sp["_imgcss"]}">')
    out += [spark(120, 1150, 42), spark(900, 1370, 32), spark(560, 380, 24)]
    ch = "".join(f'<div class="card" style="border-radius:34px;padding:9px 20px;font-weight:700;font-size:23px;white-space:nowrap">{t(c)}</div>' for c in chips)
    out.append(f'<div style="position:absolute;left:30px;right:30px;top:1500px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">{ch}</div>')
    out.append(footer(sp, 1580))
    return "".join(out)


def render(spec_path, out_path):
    spec_path = Path(spec_path).resolve()
    base = spec_path.parent
    sp = json.loads(spec_path.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="infostory_"))
    im = Image.open(base / sp["img"]).convert("RGBA")
    if sp.get("crop"):
        im = im.crop(tuple(sp["crop"]))
    if sp.get("keep_bg"):
        im = im.convert("RGB")
        sp["_imgcss"] = "mix-blend-mode:multiply"
    else:
        if im.getextrema()[3][0] == 255:  # no transparency yet
            im = mp.remove_white_bg(im)
        im = mp.trim(im)
        sp["_imgcss"] = "filter:drop-shadow(0 30px 34px rgba(40,30,80,.28))"
    im.save(tmp / "p.png")
    mp.brand_lockup(120).save(tmp / "logo.png")
    body = callout(sp, "p.png") if sp.get("style", "callout") == "callout" else hud(sp, "p.png")
    (tmp / "s.html").write_text(f'<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>{CSS}</style></head><body><div id="c">{body}</div></body></html>')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        pg.goto((tmp / "s.html").as_uri())
        pg.wait_for_timeout(700)
        pg.screenshot(path=str(tmp / "big.png"))
        b.close()
    Image.open(tmp / "big.png").convert("RGB").resize((1080, 1920), Image.LANCZOS).save(out_path, quality=93)
    print("infostory ok", out_path)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
