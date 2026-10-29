"""Product photos -> 800x800 WebP on pure white.
   rembg mask -> largest object only -> holes filled (grille mesh keeps its pixels)
   files named *box* use the convex hull of the mask (boxes are rectangles).
   python prodimg.py <src_dir> <out_dir> [name_filter]"""
import sys, os, glob
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from rembg import remove, new_session
from scipy import ndimage
from scipy.spatial import ConvexHull

SIZE, PAD = 800, 0.07
_S = {}
def sess(name):
    if name not in _S: _S[name] = new_session(name)
    return _S[name]

def mask_of(im, model, keep_all=False):
    a = np.array(remove(im, session=sess(model), only_mask=True)) > 128
    lab, n = ndimage.label(a)
    if n > 1 and keep_all:                      # multi-object photo: keep every big part
        sizes = ndimage.sum(a, lab, range(1, n + 1))
        a = np.isin(lab, [i + 1 for i, sz in enumerate(sizes) if sz > 0.05 * sizes.max()])
    elif n > 1:
        sizes = ndimage.sum(a, lab, range(1, n + 1)); a = lab == (np.argmax(sizes) + 1)
    return ndimage.binary_fill_holes(a)

def hull(a):
    ys, xs = np.nonzero(a); pts = np.c_[xs, ys]
    h = ConvexHull(pts); poly = [tuple(map(int, pts[i])) for i in h.vertices]
    m = Image.new("L", (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    return np.array(m) > 0

def cut(path):
    im = Image.open(path).convert("RGB")
    box = "box" in os.path.basename(path)
    a = mask_of(im, "u2net" if box else "isnet-general-use", keep_all="pair" in os.path.basename(path))
    if box: a = hull(a)
    a = ndimage.binary_erosion(a, iterations=2)
    m = Image.fromarray((a * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))
    out = im.convert("RGBA"); out.putalpha(m)
    return out.crop(out.getbbox())

def place(fg):
    inner = int(SIZE * (1 - 2 * PAD))
    fg.thumbnail((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), "white")
    x, y = (SIZE - fg.width) // 2, (SIZE - fg.height) // 2
    sh = Image.new("L", (SIZE, SIZE), 0)
    sh.paste(fg.split()[3].point(lambda v: 55 if v > 128 else 0), (x + 6, y + 12))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas.paste(Image.new("RGB", (SIZE, SIZE), (150, 150, 150)), (0, 0), sh)
    canvas.paste(fg, (x, y), fg)
    return canvas

def composite(left, right, gap=0.02):
    """Main image: two cutouts (with grille / without grille) side by side on 800x800 white."""
    inner = int(SIZE * 0.96); w = int(inner * (1 - gap) / 2)
    parts = []
    for fg in (left, right):
        fg = fg.copy(); fg.thumbnail((w, inner), Image.LANCZOS); parts.append(fg)
    canvas = Image.new("RGB", (SIZE, SIZE), "white"); sh = Image.new("L", (SIZE, SIZE), 0)
    x0 = (SIZE - (parts[0].width + parts[1].width + int(inner * gap))) // 2
    xs = [x0, x0 + parts[0].width + int(inner * gap)]
    for fg, x in zip(parts, xs):
        y = (SIZE - fg.height) // 2
        sh.paste(fg.split()[3].point(lambda v: 55 if v > 128 else 0), (x + 6, y + 12), fg.split()[3].point(lambda v: 255 if v > 128 else 0))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas.paste(Image.new("RGB", (SIZE, SIZE), (150, 150, 150)), (0, 0), sh)
    for fg, x in zip(parts, xs):
        canvas.paste(fg, (x, (SIZE - fg.height) // 2), fg)
    return canvas

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]; flt = sys.argv[3] if len(sys.argv) > 3 else ""
    os.makedirs(dst, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, "*.jpg"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if flt and flt not in name: continue
        p = os.path.join(dst, name + ".webp"); place(cut(f)).save(p, "WEBP", quality=86, method=6)
        print(name, os.path.getsize(p) // 1024, "KB", flush=True)
