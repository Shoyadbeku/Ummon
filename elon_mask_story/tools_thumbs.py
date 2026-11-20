import subprocess, sys, concurrent.futures as cf
from PIL import Image
urls = [l.strip() for l in open(sys.argv[1]) if l.strip()]
for n, u in enumerate(urls, 1):
    d = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',u],capture_output=True,text=True).stdout)
    step = max(3, d / 30); ts = [round(k * step, 1) for k in range(30) if k * step < d - 1]
    def grab(t):
        o = f'th/n{n}_{t:07.1f}.jpg'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',str(t),'-i',u,'-frames:v','1','-vf',f"scale=320:-2,drawtext=text='{t}':x=4:y=4:fontsize=22:fontcolor=yellow:box=1:boxcolor=black",o])
        return o
    with cf.ThreadPoolExecutor(10) as ex: outs = list(ex.map(grab, ts))
    ims = [Image.open(o) for o in outs]; w, h = ims[0].size; cols = 6
    sheet = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(f'th/sheet{n}.jpg', quality=80); print(n, round(d), len(ims))
