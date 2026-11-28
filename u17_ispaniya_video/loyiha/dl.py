import json,subprocess,sys,os
vid=sys.argv[1]; out=f"yt/{vid}.mp4"
if os.path.exists(out): print("have",vid); sys.exit()
subprocess.run(["node","snapget.js",f"https://www.youtube.com/watch?v={vid}",f"yt/{vid}.json"],check=True)
d=json.load(open(f"yt/{vid}.json"))
vs=[v for v in d['medias'][0]['variants'] if v.get('video_codec','').startswith(('h264','avc')) and v['quality']<=2160 and v.get('audio_proxy_url')]
vs=sorted(vs,key=lambda v:-v['quality'])
if not vs: vs=sorted([v for v in d['medias'][0]['variants'] if v.get('audio_proxy_url')],key=lambda v:-v['quality'])
v=vs[0]
print(vid,v['quality'],v['video_codec'])
for k,f in (("video_proxy_url",f"yt/{vid}.v"),("audio_proxy_url",f"yt/{vid}.a")):
    size=int(v[k.replace('proxy_url','filesize')] or 0); chunk=5_000_000; open(f,'wb').close(); pos=0
    while pos<size:
        end=min(pos+chunk,size)-1
        for t in range(6):
            r=subprocess.run(["curl","-s","-L","-m","120","-r",f"{pos}-{end}","-o",f+".part",v[k]])
            if r.returncode==0 and os.path.getsize(f+".part")==end-pos+1: break
            import time; time.sleep(2+t*2)
        else: raise SystemExit(f"chunk fail {pos}")
        with open(f,'ab') as o: o.write(open(f+".part",'rb').read())
        pos=end+1
    os.remove(f+".part")
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"yt/{vid}.v","-i",f"yt/{vid}.a","-c","copy",out],check=True)
os.remove(f"yt/{vid}.v");os.remove(f"yt/{vid}.a")
print("ok",vid,os.path.getsize(out))
