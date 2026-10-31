"""Instagram highlight covers for lalehstore (1080x1920, icon in the centre circle).
Usage: python3 -I highlights.py OUTDIR"""
import sys, pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
I = {
 "new": '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>',
 "guide": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
 "car": '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
 "mic": '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>',
 "speaker": '<rect width="16" height="20" x="4" y="2" rx="2"/><circle cx="12" cy="14" r="4"/><path d="M12 6h.01"/>',
 "wifi": '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
 "plug": '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
 "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
 "truck": '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
 "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
}
ITEMS = [("01-new","new","جدیدها"),("02-guide","guide","راهنمای خرید"),("03-car","car","سیستم صوتی ماشین"),
 ("04-mic","mic","میکروفون"),("05-speaker","speaker","اسپیکر"),("06-network","wifi","مودم و شبکه"),
 ("07-power","plug","محافظ برق"),("08-reviews","heart","رضایت مشتری"),("09-shipping","truck","سفارش و ارسال"),
 ("10-warranty","shield","اصالت و گارانتی")]
import base64
def _d(f, mime): return f"data:{mime};base64," + base64.b64encode((HERE/"fonts"/f).read_bytes()).decode()
FONT = _d("Vazirmatn-Black.ttf", "font/ttf")
LAT = _d("quicksand-latin-700-normal.woff", "font/woff")
def page(icon, label):
    return f"""<html><head><style>
@font-face{{font-family:V;src:url('{FONT}')}} @font-face{{font-family:Q;src:url('{LAT}')}}
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden}}
body{{background:linear-gradient(150deg,#EC5581 0%,#9A5FC0 50%,#3E95F7 100%);position:relative}}
.glow{{position:absolute;inset:0;background:radial-gradient(circle at 50% 50%,rgba(255,255,255,.22) 0,rgba(255,255,255,0) 38%)}}
.ring{{position:absolute;left:190px;top:610px;width:700px;height:700px;border-radius:50%;
 border:6px solid rgba(255,255,255,.55);box-sizing:border-box}}
svg{{position:absolute;left:270px;top:690px;width:540px;height:540px;filter:drop-shadow(0 10px 24px rgba(40,30,90,.25))}}
.lab{{position:absolute;top:1580px;width:100%;text-align:center;font:72px V;color:#fff;direction:rtl}}
.brand{{position:absolute;top:1700px;width:100%;text-align:center;font:44px Q;color:rgba(255,255,255,.8);letter-spacing:2px}}
</style></head><body><div class="glow"></div><div class="ring"></div>
<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{I[icon]}</svg>
<div class="lab">{label}</div><div class="brand">lalehstore</div></body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":1080,"height":1920})
    for fn, icon, label in ITEMS:
        pg.set_content(page(icon, label)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT/f"{fn}.jpg"), type="jpeg", quality=92)
    b.close()
print("ok", len(ITEMS))
