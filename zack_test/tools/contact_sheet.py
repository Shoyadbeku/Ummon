"""Tile all frame_*.png in a directory side by side into sheet.png."""
import sys,glob
from PIL import Image
d=sys.argv[1];fs=sorted(glob.glob(d+'/frame_*.png'));ims=[Image.open(f) for f in fs]
W=sum(i.width for i in ims);c=Image.new('RGB',(W,ims[0].height));x=0
for i in ims:c.paste(i,(x,0));x+=i.width
c.save(d+'/sheet.png')
