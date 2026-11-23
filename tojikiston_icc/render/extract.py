# Har bir klipni 25 fps JPEG kadrlarga ajratadi: frames/<id>/00001.jpg ...
import json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
media,out=sys.argv[1],sys.argv[2]
clips=json.load(open(os.path.join(os.path.dirname(__file__),'clips.json')))
def job(item):
    cid,c=item; d=os.path.join(out,cid); os.makedirs(d,exist_ok=True)
    if os.path.exists(os.path.join(d,'00001.jpg')): return cid,'skip'
    vf="fps=25"
    if c.get('crop43'): vf="crop=ih*4/3:ih,"+vf
    if not c.get('lowres'): vf+=",scale=1920:1080:flags=lanczos"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c['ss']),'-i',os.path.join(media,c['src']),'-t',str(c['t']),'-vf',vf,'-q:v','3',os.path.join(d,'%05d.jpg')],check=True)
    return cid,len(os.listdir(d))
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(job,clips.items()): print(*r)
