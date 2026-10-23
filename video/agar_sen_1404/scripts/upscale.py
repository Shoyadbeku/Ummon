import os, sys
from PIL import Image, ImageFilter
src, dst = "/opt/work/gen/img", "/opt/work/rv/public/img"; os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(src)):
    o = os.path.join(dst, f.replace(".png", ".jpg"))
    if os.path.exists(o): continue
    im = Image.open(os.path.join(src, f)).convert("RGB").resize((1920, 1120), Image.LANCZOS)
    im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2)).save(o, quality=92)
