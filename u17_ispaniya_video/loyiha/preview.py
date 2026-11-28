import sys, subprocess
sys.path.insert(0,'.')
from PIL import Image
import gfx
ims=[]
for tt in sys.argv[1:]:
    t=float(tt)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",f"{t:.3f}","-i","build/base.mp4","-frames:v","1","build/_b.png"],check=True)
    b=Image.open("build/_b.png").convert("RGBA")
    f=Image.alpha_composite(b,gfx.render(t)).convert("RGB")
    ims.append(f.resize((960,540)))
cols=2; rows=(len(ims)+1)//2
sheet=Image.new("RGB",(960*cols,540*rows))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*960,(i//cols)*540))
sheet.save("build/preview.jpg",quality=85)
