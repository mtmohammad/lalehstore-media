import sys,os; os.environ["CUT_DIR"]="/home/claude/work/cut"
sys.path.insert(0,"/home/claude/lalehstore-media/tools/blog")
from sysgfx import *
B="<bdi dir='ltr'>%s</bdi>"
jobs={}
jobs["best-car-component-1405-cover"]=article_cover("بهترین کامپوننت ماشین<br>با آمپ و بدون آمپ","راهنمای انتخاب ۱۴۰۵",["ref-6530cx","gto609c","kfc-ps170c"],ac="#ff6a00")
jobs["infinity-6530cx-vs-kenwood-ps170c"]=compare_banner("کامپوننت بدون آمپ یا با آمپ؟",
  dict(cut="ref-6530cx",name="Infinity REF-6530cx"),dict(cut="kfc-ps170c",name="Kenwood KFC-PS170C"),
  [("توان RMS (وات)","90","80"),("مقاومت (اهم)","3","4"),("حساسیت (دسی بل)","93","86"),("پاسخ فرکانسی",B%"53Hz – 21kHz",B%"58Hz – 22kHz"),("مناسب برای","پخش یا آمپ","آمپلی فایر")],ac="#c9a227")
jobs["component-kenwood-ps170c-ps804ex-system"]=system_banner("کامپوننت کنوود با آمپ ۴ کانال کنوود",
  "ووفر در درب جلو، تیوتر بالای درب یا روی داشبورد، آمپ زیر صندلی",
  [dict(cut="kfc-ps170c",label="کامپوننت کنوود",name="<bdi dir=ltr style=white-space:nowrap>KFC-PS170C</bdi><br>توان ۸۰ وات RMS<br>مقاومت ۴ اهم",pos="fl"),
   dict(cut="kac-ps804ex",label="آمپ ۴ کانال کنوود",name="<bdi dir=ltr style=white-space:nowrap>KAC-PS804EX</bdi><br>۴ × ۸۰ وات RMS<br>در ۴ اهم",pos="seat")],
  ac="#e8341c",note="دو کانال آمپ برای کامپوننت جلو؛ دو کانال دیگر برای باند عقب یا بریج برای ساب")
jobs["jbl-gto609c-component-banner"]=product_banner("jbl","GTO609C","کامپوننت جی بی ال <b>GTO609C</b><br>۳ اهم با حساسیت ۹۲ دسی بل",
  [("90W","توان RMS"),("3Ω","مقاومت"),("92dB","حساسیت"),("270W","توان پیک")],"gto609c","کامپوننت ۱۶ سانت با کراس اوور جدا")
w,h,html=jobs["component-kenwood-ps170c-ps804ex-system"]
html=html.replace("grid-template-columns:1fr 1fr","grid-template-columns:1fr").replace(".it img{width:150px",".it img{width:230px")
jobs["component-kenwood-ps170c-ps804ex-system"]=(w,h,html)
render(jobs,"/home/claude/work/out/")
