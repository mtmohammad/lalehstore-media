"""Content graphics for car-audio products (RTL Persian, Playwright -> WebP):
   product_banner()  1200x600  brand-styled hero banner
   system_banner()   1200x720  top view of a car with numbered positions + legend of the products
   compare_banner()  1200x720  two products side by side with spec rows
   Use: from sysgfx import render, product_banner, system_banner, compare_banner"""
import base64, os, io
from playwright.sync_api import sync_playwright
from PIL import Image

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
CUT = os.environ.get("CUT_DIR", "cut") + "/"


def b64(p, m=None):
    m = m or ("image/png" if p.endswith(".png") else "image/webp" if p.endswith(".webp") else "image/jpeg")
    return f"data:{m};base64," + base64.b64encode(open(p, "rb").read()).decode()


FONTS = f"""@font-face{{font-family:V;src:url({b64(FD+'/Vazirmatn-Black.ttf','font/ttf')});font-weight:900}}
@font-face{{font-family:V;src:url({b64(FD+'/Vazirmatn-Bold.ttf','font/ttf')});font-weight:700}}
@font-face{{font-family:V;src:url({b64(FD+'/Vazirmatn-Medium.ttf','font/ttf')});font-weight:500}}
@font-face{{font-family:MI;src:url({b64(FD+'/Michroma.woff2','font/woff2')})}}
*{{margin:0;box-sizing:border-box}} body{{font-family:V;overflow:hidden;position:relative}}"""

BRAND = {  # bg, accent, logo text
    "kenwood": ("#0d0d0f", "#e8341c", "KENWOOD"),
    "pioneer": ("#0b0f14", "#1e9bd7", "Pioneer"),
    "nakamichi": ("#101010", "#d71920", "Nakamichi"),
    "jbl": ("#111111", "#ff6a00", "JBL"),
    "infinity": ("#0e1116", "#c9a227", "INFINITY"),
}


def img(name):
    p = CUT + name + ".png"
    return b64(p)


# ---------------------------------------------------------------- product banner
def product_banner(brand, model, title_html, chips, cut, foot):
    bg, ac, logo = BRAND[brand]
    ch = "".join(f'<div class="c"><b>{b}</b><span>{s}</span></div>' for b, s in chips)
    return 1200, 600, f"""<html><head><style>{FONTS}
body{{width:1200px;height:600px;background:radial-gradient(ellipse at 28% 55%,#2b2c30 0,{bg} 62%,#050506 100%)}}
.glow{{position:absolute;left:330px;top:310px;width:640px;height:640px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient({ac}40,#0000 62%)}}
.p{{position:absolute;left:330px;top:300px;transform:translate(-50%,-50%);max-width:560px;max-height:430px;filter:drop-shadow(0 26px 26px #000)}}
.brand{{position:absolute;right:60px;top:42px;font-family:MI;font-size:38px;color:#fff;letter-spacing:5px}}
.model{{position:absolute;right:60px;top:100px;font-family:MI;font-size:24px;color:{ac};letter-spacing:3px;direction:ltr}}
.t{{position:absolute;right:60px;top:160px;width:540px;direction:rtl;text-align:right;color:#fff}}
.t h1{{font-weight:900;font-size:42px;line-height:1.35}} .t h1 b{{color:{ac}}}
.chips{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}
.c{{border:1.5px solid #ffffff3a;border-radius:10px;padding:8px 14px;background:#ffffff0d}}
.c b{{display:block;font-family:MI;font-size:19px;color:#fff;direction:ltr;text-align:right}}
.c span{{font-size:14px;color:#c9c9cc;font-weight:500}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:58px;background:{ac};display:flex;align-items:center;justify-content:space-between;padding:0 60px;direction:rtl;color:#fff}}
.foot .w{{font-weight:700;font-size:20px}} .foot .s{{font-family:MI;font-size:14px;letter-spacing:5px;direction:ltr}}
</style></head><body><div class="glow"></div><img class="p" src="{img(cut)}">
<div class="brand">{logo}</div><div class="model">{model}</div>
<div class="t"><h1>{title_html}</h1><div class="chips">{ch}</div></div>
<div class="foot"><span class="w">{foot}</span><span class="s">LALEHSTORE.COM</span></div></body></html>"""


# ---------------------------------------------------------------- system banner
POS = {  # marker positions on the car drawing (x,y inside the 420x660 car box)
    "dash": (210, 168), "fl": (52, 250), "fr": (368, 250), "rl": (52, 410), "rr": (368, 410),
    "deck": (210, 520), "trunk": (210, 600), "seat": (290, 300), "pillar": (95, 150),
}


def car_svg(marks, ac):
    m = ""
    for i, pos in marks:
        x, y = POS[pos]
        m += (f'<circle cx="{x}" cy="{y}" r="22" fill="{ac}" stroke="#fff" stroke-width="4"/>'
              f'<text x="{x}" y="{y+8}" text-anchor="middle" font-family="V" font-weight="900" font-size="22" fill="#fff">{i}</text>')
    return f"""<svg width="420" height="660" viewBox="0 0 420 660">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#d9dde3"/><stop offset=".5" stop-color="#f4f6f8"/><stop offset="1" stop-color="#d9dde3"/></linearGradient></defs>
<path d="M110 30 Q210 0 310 30 Q372 52 380 130 L392 560 Q392 640 300 650 L120 650 Q28 640 28 560 L40 130 Q48 52 110 30 Z" fill="url(#g)" stroke="#9aa3ad" stroke-width="3"/>
<path d="M92 120 Q210 92 328 120 L312 196 Q210 178 108 196 Z" fill="#7f8b97" opacity=".55"/>
<path d="M112 468 Q210 486 308 468 L322 540 Q210 560 98 540 Z" fill="#7f8b97" opacity=".45"/>
<rect x="150" y="150" width="120" height="34" rx="6" fill="#2b3036"/>
<rect x="92" y="222" width="96" height="110" rx="26" fill="#bfc6ce"/><rect x="232" y="222" width="96" height="110" rx="26" fill="#bfc6ce"/>
<rect x="92" y="352" width="236" height="100" rx="28" fill="#bfc6ce"/>
<rect x="34" y="210" width="10" height="250" rx="4" fill="#9aa3ad"/><rect x="376" y="210" width="10" height="250" rx="4" fill="#9aa3ad"/>
<path d="M100 572 L320 572 L330 636 L90 636 Z" fill="#e6e9ed" stroke="#b4bcc5" stroke-width="2"/>
{m}</svg>"""


def system_banner(title, subtitle, items, ac="#e8341c", note=""):
    """items: list of dict(cut, label, name, pos)"""
    MIR = {"fl": "fr", "rl": "rr"}
    marks = []
    for i, it in enumerate(items):
        marks.append((i + 1, it["pos"]))
        if it["pos"] in MIR: marks.append((i + 1, MIR[it["pos"]]))
    rows = "".join(
        f'<div class="it"><div class="n" style="background:{ac}">{i+1}</div>'
        f'<img src="{img(it["cut"])}"><div class="tx"><b>{it["label"]}</b><span>{it["name"]}</span></div></div>'
        for i, it in enumerate(items))
    return 1200, 720, f"""<html><head><style>{FONTS}
body{{width:1200px;height:720px;background:linear-gradient(135deg,#f7f8fa,#e9edf2)}}
.car{{position:absolute;left:46px;top:22px;transform:scale(.94);transform-origin:top left}}
.h{{position:absolute;right:50px;top:36px;width:680px;direction:rtl;text-align:right}}
.h h1{{font-weight:900;font-size:34px;color:#111;line-height:1.3}} .h p{{font-weight:500;font-size:19px;color:#555;margin-top:6px}}
.list{{position:absolute;right:50px;top:150px;width:680px;direction:rtl;display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.it{{display:flex;align-items:center;gap:12px;background:#fff;border-radius:16px;padding:10px 14px;box-shadow:0 6px 18px #0000001a;height:172px}}
.n{{flex:0 0 38px;height:38px;border-radius:50%;color:#fff;font-weight:900;font-size:20px;display:flex;align-items:center;justify-content:center}}
.it img{{width:150px;height:130px;object-fit:contain}}
.tx b{{display:block;font-weight:900;font-size:18px;color:#111;line-height:1.35}} .tx span{{display:block;font-weight:500;font-size:15px;color:#444;direction:rtl;margin-top:4px}}
.note{{position:absolute;right:50px;bottom:60px;width:680px;direction:rtl;text-align:right;font-weight:700;font-size:16px;color:#333}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:46px;background:#111;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 50px;direction:rtl}}
.foot b{{font-size:16px}} .foot s{{text-decoration:none;font-family:MI;font-size:13px;letter-spacing:5px;direction:ltr}}
</style></head><body><div class="car">{car_svg(marks, ac)}</div>
<div class="h"><h1>{title}</h1><p>{subtitle}</p></div><div class="list">{rows}</div>
<div class="note">{note}</div>
<div class="foot"><b>پیشنهاد چیدمان سیستم صوتی لاله استور</b><s>LALEHSTORE.COM</s></div></body></html>"""


# ---------------------------------------------------------------- compare banner
def compare_banner(title, a, b, rows, ac="#e8341c"):
    """a/b: dict(cut, name); rows: list of (label, a_value, b_value)"""
    tr = "".join(f'<tr><td class="v">{x}</td><th>{l}</th><td class="v">{y}</td></tr>' for l, x, y in rows)
    return 1200, 720, f"""<html><head><style>{FONTS}
body{{width:1200px;height:720px;background:#fff}}
.h{{position:absolute;top:26px;left:0;right:0;text-align:center;direction:rtl;font-weight:900;font-size:32px;color:#111}}
.p{{position:absolute;top:90px;width:330px;height:220px;display:flex;flex-direction:column;align-items:center}}
.p img{{width:300px;height:180px;object-fit:contain;filter:drop-shadow(0 12px 14px #0003)}}
.p b{{margin-top:6px;font-family:MI;font-size:16px;color:#111;direction:ltr}}
.pa{{right:90px}} .pb{{left:90px}}
.vs{{position:absolute;top:160px;left:560px;width:80px;height:80px;border-radius:50%;background:{ac};color:#fff;font-family:MI;font-size:24px;display:flex;align-items:center;justify-content:center}}
table{{position:absolute;top:330px;left:70px;width:1060px;border-collapse:separate;border-spacing:0 8px;direction:rtl}}
th{{width:300px;background:#111;color:#fff;font-weight:700;font-size:18px;padding:10px;border-radius:10px}}
td.v{{width:380px;background:#f1f3f6;text-align:center;font-weight:700;font-size:18px;color:#222;padding:10px;border-radius:10px;direction:rtl}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:40px;background:{ac};color:#fff;display:flex;align-items:center;justify-content:center;font-family:MI;font-size:13px;letter-spacing:5px}}
</style></head><body><div class="h">{title}</div>
<div class="p pa"><img src="{img(a['cut'])}"><b>{a['name']}</b></div>
<div class="vs">VS</div>
<div class="p pb"><img src="{img(b['cut'])}"><b>{b['name']}</b></div>
<table>{tr}</table><div class="foot">LALEHSTORE.COM</div></body></html>"""


# ---------------------------------------------------------------- article cover (featured image)
def article_cover(title, kicker, cuts, ac="#e8341c", brand_line="LALEHSTORE.COM"):
    """1200x675 featured image: kicker pill + title (RTL) on the right, 1-3 product cutouts on the left.
       cuts: list of cutout names in CUT (no .png). Cutouts are never scaled above their native size."""
    pos = [("left:40px;top:150px;max-width:420px;max-height:360px", ),
           ("left:300px;top:330px;max-width:300px;max-height:300px", ),
           ("left:60px;top:400px;max-width:260px;max-height:240px", )]
    imgs = "".join(f'<img class="p" style="{pos[i][0]}" src="{img(c)}">' for i, c in enumerate(cuts[:3]))
    return 1200, 675, f"""<html><head><style>{FONTS}
body{{width:1200px;height:675px;background:radial-gradient(ellipse at 28% 58%,#2d2e33 0,#0c0c0e 62%,#050506 100%)}}
.glow{{position:absolute;left:320px;top:380px;width:760px;height:620px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient({ac}38,#0000 62%)}}
.p{{position:absolute;filter:drop-shadow(0 22px 22px #000c)}}
.t{{position:absolute;right:64px;top:0;bottom:70px;width:560px;display:flex;flex-direction:column;justify-content:center;direction:rtl;text-align:right;color:#fff}}
.k{{align-self:flex-start;background:{ac};border-radius:30px;padding:6px 18px;font-weight:700;font-size:20px}}
.t h1{{font-weight:900;font-size:50px;line-height:1.4;margin-top:22px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:56px;background:{ac};display:flex;align-items:center;justify-content:flex-end;padding:0 56px;color:#fff;font-family:MI;font-size:14px;letter-spacing:5px}}
</style></head><body><div class="glow"></div>{imgs}<div class="t"><span class="k">{kicker}</span><h1>{title}</h1></div><div class="foot">{brand_line}</div></body></html>"""


def render(jobs, out_dir="out/"):
    """jobs: dict filename -> (w,h,html)"""
    os.makedirs(out_dir, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page()
        for name, (w, h, html) in jobs.items():
            pg.set_viewport_size({"width": w, "height": h}); pg.set_content(html); pg.wait_for_timeout(400)
            png = io.BytesIO(pg.screenshot())
            Image.open(png).convert("RGB").save(out_dir + name + ".webp", "WEBP", quality=88)
            print(name)
        br.close()
