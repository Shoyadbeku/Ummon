import sys, time
sys.path.insert(0, sys.argv[1])
import sb
from PIL import Image
out = sys.argv[2]; ts = [float(x) for x in sys.argv[3:]]
ims = []
for t in ts:
    tl = sb.timeline()  # fresh sources per still (videos seek)
    t0 = time.time(); im = tl.frame(t); print(t, round(time.time() - t0, 2), flush=True)
    ims.append(im.resize((640, 360)))
cols = 3; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (640 * cols, 360 * rows))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
sheet.save(out)
