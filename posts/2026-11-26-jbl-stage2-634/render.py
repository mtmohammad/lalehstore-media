import sys,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
sys.path.insert(0,'/workspace/lalehstore-media/tools')
import studio as st, music
W,H=1080,1920; out=Path(__file__).resolve().parent
P=(255,0,103); C=(255,247,235)
def ease(t):return st.in_out_cubic(st.clamp(t))
def txt(s,sz=80,color=C):return st.KText(s,sz,color,max_w=920,lines=1)
lines=[
[txt('صدای ماشینت رو ارتقا بده',74),txt('تخفیف ویژه بلک‌فرایدی',56,P)],
[txt('صندوقت کم‌عمقه؟',96),txt('ساب کم‌عمق جی‌بی‌ال',60,P),txt('میلی‌متر عمق نصب',43)],
[txt('فرصت محدوده',110),txt('۳ تا ۶ آذر',80,P),txt('از تخفیف‌های بلک‌فرایدی استفاده کن',47)],
[txt('وقت انتخابه',100),txt('مدل ماشینت رو دایرکت کن',63,P),txt('برای انتخاب ساب راهنماییت کنیم',45)]]
eng=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',166)
engsmall=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',34)
num=ImageFont.truetype(str(st.HERE/'fonts/Vazirmatn-Black.ttf'),210)
product=Image.open('/tmp/bfclean.png').convert('RGBA')
product=product.resize((486,630),Image.Resampling.LANCZOS)
yy,xx=np.mgrid[:H,:W];base=np.zeros((H,W,3),dtype=np.uint8)
g=np.exp(-((xx-540)**2/500**2+(yy-1250)**2/580**2))
for c,b in enumerate([7,6,10]):base[:,:,c]=b+g*[36,4,22][c]
bg=Image.fromarray(base).convert('RGBA');d=ImageDraw.Draw(bg)
for x in [-700,200,1100,2000]:
 d.polygon([(x,0),(x+240,0),(x-700,H),(x-940,H)],fill=(15,13,20))
 d.line((x+240,0,x-700,H),fill=(55,25,43),width=2)
def paste(im,p,cx,cy,a=1):
 if p is not None:im.alpha_composite(st.with_alpha(p,a) if a<1 else p,(int(cx-p.width/2),int(cy-p.height/2)))
def engword(word,color):
 im=Image.new('RGBA',(1000,225));d=ImageDraw.Draw(im);d.text((500,112),word,font=eng,anchor='mm',fill=color);return im
black=engword('BLACK',C);friday=engword('FRIDAY',P)
# A wide soft sweep and a narrow bright core create the light wipe.
strip=Image.new('RGBA',(380,H))
ar=np.zeros((H,380,4),dtype=np.uint8)
for i in range(380):
 a=math.exp(-((i-190)/55)**2);ar[:,i,:3]=[255,32+int(180*a),125+int(115*a)];ar[:,i,3]=int(a*190)
strip=Image.fromarray(ar)

products=[]
for i in range(4):
 p=Image.open(out/f'product-{i}.png').convert('RGBA')
 ratio=min(860/p.width,640/p.height)
 products.append(p.resize((int(p.width*ratio),int(p.height*ratio)),Image.Resampling.LANCZOS))
copy=[
 [txt('باند جی‌بی‌ال تخفیف خورد!',76),txt('تخفیف ویژه بلک‌فرایدی',65,P)],
 [txt('وقت ارتقای صدای ماشینته',75),txt('باند جی‌بی‌ال Stage2',68,P)],
 [txt('فرصت محدوده',105),txt('از تخفیف‌ها استفاده کن',66,P),txt('کمپین تا جمعه ۶ آذر',48)],
 [txt('همین حالا از سایت سفارش بده',66),txt('یا برای خرید',63),txt('دایرکت پیام بده',79,P)]]
def scene(j,t):
 im=bg.copy()
 entry=ease((t+.05)/.75)
 duration=3 if j==3 else 5
 leave=ease((t-(duration-.65))/.65)
 visible=1-leave
 # Separate product and text stages prevent any collision throughout the motion.
 dy=18*math.sin(t) if j==0 else 0
 dx=[0,1100,-1100,1100][j]*(1-entry)-1100*leave
 first=[0,1,2,0][j]
 second=[1,3,0,1][j]
 p=products[first]
 if t>=2.2 and j<3:
  canvas=Image.new('RGBA',(900,660))
  paste(canvas,products[first],450,330,1-ease((t-2.2)/.32))
  paste(canvas,products[second],450,330,ease((t-2.2)/.32))
  p=canvas
 zoom=1+.025*math.sin(t*.8)
 p=p.resize((int(p.width*zoom),int(p.height*zoom)),Image.Resampling.LANCZOS)
 halo=Image.new('RGBA',(W,H));hd=ImageDraw.Draw(halo)
 hd.ellipse((180,1050,900,1470),outline=(*P,140),width=10)
 im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(20)))
 paste(im,p,540+dx,1205+dy+6*math.sin(t*1.2),visible)
 # Highlights move around the photograph without changing its physical shape.
 beam=Image.new('RGBA',(W,H));bd=ImageDraw.Draw(beam)
 lx=int(-300+t/4.5*1700)
 bd.line((lx-100,1510,lx+240,890),fill=(*P,130),width=26)
 im.alpha_composite(beam.filter(ImageFilter.GaussianBlur(28)))
 textlayer=Image.new('RGBA',(W,760))
 td=ImageDraw.Draw(textlayer)
 if j==0:
  ys=[300,590]
  label=Image.new('RGBA',(1000,120));ImageDraw.Draw(label).text((500,60),'JBL STAGE2 634',font=engsmall.font_variant(size=63),anchor='mm',fill=C)
  paste(textlayer,label,540+1000*leave,445,visible)
 elif j==1:ys=[300,520]
 elif j==2:ys=[300,475,650]
 else:ys=[280,450,600]
 for n,(k,y) in enumerate(zip(copy[j],ys)):
  # The complete hook and offer are visible from frame zero for this test.
  p=k.full if j==0 else k.frame(t-.12-n*.15)
  paste(textlayer,p,540+1000*leave,y,visible)
 # Product stays below y=870; text is clipped at y=850.
 im.alpha_composite(textlayer,(0,90))
 d=ImageDraw.Draw(im)
 d.text((540,145),'lalehstore',font=engsmall,anchor='mm',fill=C)
 d.text((540+int(15*math.sin(t)),220),'BLACK FRIDAY',font=engsmall.font_variant(size=38),anchor='mm',fill=P)
 d.line((95,1640,985,1640),fill=P,width=2)
 d.text((540,1720),'lalehstore.com',font=engsmall.font_variant(size=43),anchor='mm',fill=C)
 return im
def frame(t):
 j=min(3,int(t/5));lt=t-j*5
 im=scene(j,lt)
 # A soft light sweep bridges the independently exiting and entering elements.
 if j>0 and lt<.65:
  q=ease(lt/.65)
  im.alpha_composite(strip,(int(-380+q*(W+760)),0))
 return im.convert('RGB')
times=[0.0,1.6,2.5,4.6,5.3,6.3,10.7,15.7,17.2]
for t in times:frame(t).save(out/f'preview-{t}.jpg',quality=92)
if '--preview' in sys.argv:sys.exit()
audio,_=music.make(18,[5,10,15],'house',2611)
music.write_wav('/tmp/bfr/approved.wav',audio)
p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','24','-i','-','-i','/tmp/bfr/approved.wav','-c:v','libx264','-threads','3','-preset','fast','-crf','21','-pix_fmt','yuv420p','-af','volume=0.7,afade=t=out:st=17:d=1','-c:a','aac','-t','18','-movflags','+faststart',str(out/'reel.mp4')],stdin=subprocess.PIPE)
for k in range(432):p.stdin.write(frame(k/24).tobytes())
p.stdin.close();sys.exit(p.wait())
