import sys, subprocess, io
from gfx import *
import scenes as SN, render as R
ims=[]
for i,sc in enumerate(SN.SC):
    dur=R.nframes(sc)/FPS; t=dur*float(sys.argv[1]) if len(sys.argv)>1 else dur*0.75
    if sc['kind']=='clip':
        png=subprocess.check_output(['ffmpeg','-loglevel','error','-ss',str(sc['ss']+t*sc['speed']),'-i',sc['src'],'-frames:v','1','-vf',f'scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2','-f','image2pipe','-vcodec','png','-'])
        im=Image.open(io.BytesIO(png)).convert('RGBA'); vignette(im)
        if sc.get('overlay'): sc['overlay'](im,t,dur)
    else:
        im=Image.new('RGBA',(W,H),(0,0,0,255)); sc['draw'](im,t,dur)
    if sc.get('tag'): loc_tag(im,sc['tag'],t,dur+.4)
    cr=R.scene_credit(sc)
    if cr: credit(im,cr,t,dur+.4)
    d=ImageDraw.Draw(im); d.text((10,10),f"#{i} {sc['t0']:.1f}",font=F('Inter-Bold',40),fill=(255,0,255,255))
    ims.append(im.convert('RGB').resize((640,360)))
for k in range(0,len(ims),12):
    sheet=Image.new('RGB',(640*3,360*4))
    for j,im in enumerate(ims[k:k+12]): sheet.paste(im,((j%3)*640,(j//3)*360))
    sheet.save(f'sheets/prev_{k//12}.jpg',quality=85)
print(len(ims))
