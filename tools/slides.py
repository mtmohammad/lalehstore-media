"""lalehstore NEWS / EDUCATION carousel (1080x1350 image slides), magazine layout in the lalehstore LIGHT brand theme.

Mohammad's request (2026-11-02): tech-news and educational posts are image CAROUSELS (not reels),
laid out like the big Persian tech pages (Zoomit / Digiato: kicker line, big bold headline with
highlighted words, big hero visual, «ورق بزنید» hint, numbered inner slides) BUT in lalehstore's own
theme (Mohammad: «تم اصلی رعایت بشه»): light background with soft pink/blue glows, brand-gradient
pills and highlights, white cards, Vazirmatn, lalehstore logo + @lalehstoree footer.

Spec JSON (paths relative to the spec file):
{
  "kind": "news" | "edu",
  "cover": {
    "kicker": "خبر تکنولوژی",                       # gradient pill above the title
    "title": "سامسونگ *هندزفری گیره ای* ساخت",       # *...* = brand-gradient highlight; 2-3 lines max
    "hero": "icon:headphones" | "product.webp",      # 3D icon from tools/icons or a store photo (white bg removed)
    "hero2": "icon:sparkles",                        # optional smaller second visual
    "badge": "Galaxy Buds On"                        # optional glass label over the hero
  },
  "slides": [                                        # 2-4 inner slides
    {"title": "روی لاله گوش *گیره* میشه",
     "big": "9.5h", "big_sub": "پخش موسیقی",           # optional big number/keyword card
     "visual": "icon:battery" | "product.webp",        # optional visual (right side / top)
     "points": ["...", "..."]}                         # 2-4 short lines (max ~55 chars)
  ],
  "outro": {"title": "تو کدوم رو *ترجیح* میدی؟", "sub": "نظرت رو کامنت کن", "cta": "ذخیره کن"},
  "source": "audioXpress"                            # shown small on the last inner slide + outro
}

Usage:  python3 -I slides.py spec.json OUT_DIR      -> OUT_DIR/slide_01.jpg ...
"""
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_post as mp  # noqa: E402

mp.FONT_DIR = str(HERE / "fonts")
mp.LATIN_FONT = str(HERE / "fonts" / "quicksand-latin-700-normal.woff")

W, H = 1080, 1350
YELLOW = "#FFD84D"
HANDLE = "@lalehstoree"


def b64png(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def font_face(name, file):
    data = base64.b64encode((HERE / "fonts" / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data});}}"


def visual(ref: str, base: Path, size: int):
    """Return (data_uri, is_icon)."""
    if ref.startswith("icon:"):
        im = Image.open(HERE / "icons" / f"{ref[5:]}.webp").convert("RGBA")
        im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
        return b64png(im), True
    im = mp.trim(mp.remove_white_bg(Image.open(base / ref).convert("RGB")))
    if max(im.size) > size * 1.6:
        im.thumbnail((int(size * 1.6), int(size * 1.6)), Image.LANCZOS)
    return b64png(im), False


def rich(text: str) -> str:
    t = html.escape(text)
    # isolate Latin runs so bidi stays correct inside Persian lines (before adding any tags)
    t = re.sub(r"([A-Za-z0-9][A-Za-z0-9 .+\-/×%:]*[A-Za-z0-9%+]|[A-Za-z0-9])",
               r'<bdi dir="ltr">\1</bdi>', t)
    return re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', t)


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;background:#F6F7FB;font-family:'Vaz';color:#1C1E2A;direction:rtl}
.s{position:relative;width:1080px;height:1350px;overflow:hidden}
.bg{position:absolute;inset:0;background:
  radial-gradient(760px 640px at 0% 0%, rgba(236,85,129,.30), transparent 65%),
  radial-gradient(900px 760px at 100% 100%, rgba(62,149,247,.32), transparent 65%),
  radial-gradient(700px 500px at 100% 20%, rgba(62,149,247,.10), transparent 70%),
  #F6F7FB;}
.grid{position:absolute;left:-40%;right:-40%;bottom:-6%;height:44%;
  background-image:linear-gradient(rgba(62,149,247,.20) 2px,transparent 2px),linear-gradient(90deg,rgba(236,85,129,.16) 2px,transparent 2px);
  background-size:90px 90px;transform:perspective(700px) rotateX(64deg);transform-origin:50% 100%;
  -webkit-mask-image:linear-gradient(to top, rgba(0,0,0,.85), transparent 85%);}
.dots{position:absolute;inset:0}
.dots i{position:absolute;border-radius:50%;background:linear-gradient(135deg,PINK,BLUE)}
.vign{position:absolute;inset:0}
.top{display:none}
.kicker{position:absolute;top:92px;left:50%;transform:translateX(-50%);white-space:nowrap;color:#fff;font-weight:900;font-size:34px;
  padding:10px 34px;border-radius:40px;background:linear-gradient(90deg,BLUE,PINK);box-shadow:0 10px 30px rgba(236,85,129,.30)}
.title{position:absolute;top:178px;left:56px;right:56px;text-align:center;font-weight:900;font-size:72px;line-height:1.38;color:#1C1E2A}
.hl{white-space:nowrap;background:linear-gradient(90deg,PINK,#9B6BD6,BLUE);-webkit-background-clip:text;background-clip:text;color:transparent}
.swipe{position:absolute;left:50%;transform:translateX(-50%);font-weight:700;font-size:32px;display:flex;gap:14px;align-items:center;color:#1C1E2A;
  background:#fff;padding:12px 30px;border-radius:40px;box-shadow:0 10px 30px rgba(40,40,90,.14)}
.swipe b{display:inline-flex;width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,PINK,BLUE);color:#fff;align-items:center;justify-content:center;font-size:30px;line-height:1}
.hero{position:absolute;left:50%;transform:translateX(-50%);display:flex;align-items:center;justify-content:center}
.hero img{max-width:100%;max-height:100%;object-fit:contain}
.glow{position:absolute;left:50%;transform:translateX(-50%);border-radius:50%;
  background:radial-gradient(closest-side, rgba(255,255,255,.98), rgba(255,255,255,.75) 45%, transparent 75%);filter:blur(6px)}
.ring{position:absolute;left:50%;transform:translateX(-50%) perspective(600px) rotateX(70deg);border-radius:50%;
  border:4px solid rgba(236,85,129,.55);box-shadow:0 0 40px rgba(236,85,129,.45), inset 0 0 40px rgba(236,85,129,.25)}
.ring.b{border-color:rgba(62,149,247,.6);box-shadow:0 0 50px rgba(62,149,247,.5), inset 0 0 50px rgba(62,149,247,.3)}
.badge{position:absolute;left:50%;transform:translateX(-50%);font-family:'Vaz';font-weight:900;font-size:44px;direction:ltr;white-space:nowrap;color:#1C1E2A;
  padding:14px 38px;border-radius:26px;background:rgba(255,255,255,.92);box-shadow:0 14px 40px rgba(40,40,90,.18)}
.foot{position:absolute;bottom:42px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center;direction:ltr}
.foot img{height:50px}
.foot span{font-weight:700;font-size:30px;color:#6E7284}
.num{position:absolute;top:84px;right:64px;width:120px;height:120px;border-radius:30px;background:linear-gradient(135deg,PINK,BLUE);color:#fff;
  font-weight:900;font-size:66px;display:flex;align-items:center;justify-content:center;direction:ltr;box-shadow:0 14px 40px rgba(236,85,129,.30)}
.kick2{position:absolute;top:118px;left:64px;color:#6E7284;font-weight:700;font-size:30px}
.ititle{position:absolute;top:240px;left:64px;right:64px;font-weight:900;font-size:62px;line-height:1.4;text-align:right;color:#1C1E2A}
.panel{position:absolute;left:64px;right:64px;display:flex;flex-direction:column;gap:22px}
.pt{display:flex;gap:22px;align-items:center;background:#fff;border-radius:28px;padding:24px 30px;font-weight:700;font-size:38px;line-height:1.5;
  box-shadow:0 12px 34px rgba(40,40,90,.10)}
.pt i{flex:none;width:20px;height:20px;border-radius:50%;background:linear-gradient(135deg,PINK,BLUE)}
.big{position:absolute;left:64px;text-align:center;border-radius:36px;padding:28px 40px;background:#fff;box-shadow:0 16px 44px rgba(40,40,90,.14)}
.big .v{font-weight:900;font-size:120px;line-height:1.15;direction:ltr;unicode-bidi:isolate;
  background:linear-gradient(90deg,PINK,#9B6BD6,BLUE);-webkit-background-clip:text;background-clip:text;color:transparent}
.big .u{white-space:nowrap;font-weight:700;font-size:32px;color:#6E7284;margin-top:4px}
.vis{position:absolute;display:flex;align-items:center;justify-content:center}
.vis img{max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 26px 30px rgba(40,40,90,.25))}
.src{position:absolute;bottom:118px;right:64px;font-weight:700;font-size:28px;color:#6E7284}
.otitle{position:absolute;top:470px;left:60px;right:60px;text-align:center;font-weight:900;font-size:78px;line-height:1.4}
.osub{position:absolute;top:720px;left:60px;right:60px;text-align:center;font-weight:700;font-size:42px;color:#6E7284}
.cta{position:absolute;top:840px;left:50%;transform:translateX(-50%);display:flex;gap:24px;direction:rtl}
.cta div{font-weight:900;font-size:40px;padding:22px 44px;border-radius:50px;white-space:nowrap}
.cta .a{background:linear-gradient(90deg,BLUE,PINK);color:#fff;box-shadow:0 12px 34px rgba(236,85,129,.3)}
.cta .b{background:#fff;color:#1C1E2A;box-shadow:0 12px 34px rgba(40,40,90,.12)}
.biglogo{position:absolute;top:250px;left:50%;transform:translateX(-50%)}
.biglogo img{height:120px}
""".replace("PINK", "rgb(236,85,129)").replace("BLUE", "rgb(62,149,247)")


def dots(seed):
    import random
    r = random.Random(seed)
    out = []
    for _ in range(70):
        s = r.choice([2, 3, 3, 4, 6])
        out.append(f'<i style="left:{r.randint(0, 1080)}px;top:{r.randint(380, 1300)}px;width:{s}px;height:{s}px;'
                   f'opacity:{r.uniform(.12, .45):.2f}"></i>')
    return '<div class="dots">' + "".join(out) + "</div>"


def stage(inner, seed, foot, grid=True):
    return (f'<div class="s"><div class="bg"></div>{"<div class=grid></div>" if grid else ""}{dots(seed)}'
            f'<div class="vign"></div>{inner}{foot}</div>')


def cover(spec, base, foot):
    c = spec["cover"]
    hero, is_icon = visual(c["hero"], base, 620)
    tl = len(c["title"].replace("*", ""))
    hy = 430 if tl <= 22 else (510 if tl <= 44 else 590)       # below the 1-3 line headline
    hs = min(640 if is_icon else 700, 1040 - hy)
    parts = [f'<div class="glow" style="top:{hy - 40}px;width:{hs + 300}px;height:{hs + 120}px"></div>',
             f'<div class="ring" style="top:{hy + hs - 150}px;width:{hs + 40}px;height:{hs // 2}px"></div>',
             f'<div class="ring b" style="top:{hy + hs - 120}px;width:{hs + 220}px;height:{hs // 2 + 60}px;opacity:.6"></div>',
             f'<div class="hero" style="top:{hy}px;width:{hs}px;height:{hs}px">'
             f'<img src="{hero}" style="filter:drop-shadow(0 40px 46px rgba(40,40,90,.28))"></div>']
    if c.get("hero2"):
        h2, _ = visual(c["hero2"], base, 260)
        parts.append(f'<div class="hero" style="top:{hy + 40}px;left:180px;width:240px;height:240px;transform:rotate(-12deg)">'
                     f'<img src="{h2}" style="filter:drop-shadow(0 20px 26px rgba(40,40,90,.25))"></div>')
    parts.append('<div class="top"></div>')
    parts.append(f'<div class="kicker">{rich(c.get("kicker", ""))}</div>')
    parts.append(f'<div class="title">{rich(c["title"])}</div>')
    if c.get("badge"):
        parts.append(f'<div class="badge" style="top:{hy + hs - 10}px">{html.escape(c["badge"])}</div>')
    parts.append('<div class="swipe" style="bottom:118px"><b>‹</b>ورق بزنید</div>')
    return stage("".join(parts), 11, foot)


def inner(i, n, sl, spec, base, foot, last):
    parts = [f'<div class="num">{i:02d}</div>',
             f'<div class="kick2">{rich(spec["cover"].get("kicker", ""))} · {i} از {n}</div>',
             f'<div class="ititle">{rich(sl["title"])}</div>']
    y = 470 if len(sl["title"]) > 26 else 400
    has_vis = bool(sl.get("visual"))
    if sl.get("big"):
        bw = 560 if has_vis else 952
        bv = sl["big"]
        fs = 120 if len(bv) <= 5 else (100 if len(bv) <= 7 else (84 if len(bv) <= 9 else 68))
        if has_vis:
            fs = int(fs * 0.9)
        bdir = "rtl" if any("\u0600" <= ch <= "\u06ff" for ch in bv) else "ltr"
        parts.append(f'<div class="big" style="top:{y}px;width:{bw}px"><div class="v" style="font-size:{fs}px;direction:{bdir};white-space:nowrap">{html.escape(bv)}</div>'
                     f'<div class="u">{rich(sl.get("big_sub", ""))}</div></div>')
    if has_vis:
        v, is_icon = visual(sl["visual"], base, 380)
        vs = 340 if sl.get("big") else 420
        vx = 1080 - 64 - vs if not sl.get("big") else 1080 - 64 - 340
        if sl.get("big"):
            parts.append(f'<div class="vis" style="top:{y - 10}px;right:64px;width:340px;height:300px"><img src="{v}"></div>')
        else:
            parts.append(f'<div class="glow" style="top:{y - 30}px;width:640px;height:420px"></div>'
                         f'<div class="vis" style="top:{y}px;left:50%;transform:translateX(-50%);width:{vs + 200}px;height:{vs}px"><img src="{v}"></div>')
        _ = vx
    py = y + (290 if (sl.get("big") or has_vis) else 0) + (40 if (sl.get("big") or has_vis) else 0)
    if not sl.get("big") and has_vis:
        py = y + 460
    pts = "".join(f'<div class="pt"><i></i><div>{rich(p)}</div></div>' for p in sl.get("points", [])[:4])
    parts.append(f'<div class="panel" style="top:{py}px">{pts}</div>')
    if last and spec.get("source"):
        parts.append(f'<div class="src">منبع: {rich(spec["source"])}</div>')
    return stage("".join(parts), 20 + i, foot, grid=False)


def outro(spec, foot, logo_big):
    o = spec["outro"]
    parts = [f'<div class="biglogo"><img src="{logo_big}"></div>',
             f'<div class="otitle">{rich(o["title"])}</div>',
             f'<div class="osub">{rich(o.get("sub", ""))}</div>',
             '<div class="cta">'
             + (f'<div class="a">{rich(o["cta"])}</div>' if o.get("cta") else "")
             + '<div class="b">فالو کن</div></div>',
             '<div class="src" style="right:0;left:0;text-align:center;bottom:130px;direction:ltr">021-33917554 · lalehstore.com</div>']
    return stage("".join(parts), 99, foot)


def main():
    spec_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    base = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    logo = b64png(mp.brand_lockup(50))
    logo_big = b64png(mp.brand_lockup(120))
    foot = f'<div class="foot"><img src="{logo}"><span>{HANDLE}</span></div>'
    pages = [cover(spec, base, foot)]
    n = len(spec["slides"])
    for i, sl in enumerate(spec["slides"], start=1):
        pages.append(inner(i, n, sl, spec, base, foot, i == n))
    pages.append(outro(spec, foot, logo_big))
    head = ("<html><head><meta charset='utf-8'><style>" + font_face("Vaz", "Vazirmatn-Black.ttf").replace(
        "src:", "font-weight:900;src:") + font_face("Vaz", "Vazirmatn-Bold.ttf").replace(
        "src:", "font-weight:700;src:") + CSS + "</style></head><body>")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for k, body in enumerate(pages, start=1):
            pg.set_content(head + body + "</body></html>")
            pg.wait_for_timeout(250)
            pg.screenshot(path=str(out / f"slide_{k:02d}.jpg"), type="jpeg", quality=93)
        b.close()
    print(f"{len(pages)} slides -> {out}")


if __name__ == "__main__":
    main()
