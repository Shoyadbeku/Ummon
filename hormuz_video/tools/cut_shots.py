"""Storyboard bo'yicha har bir kadrni kesib, 1920x1080 / 30fps / H.264 ga keltiradi (+rang korreksiyasi)."""
import json, subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sb=json.load(open(f"{ROOT}/src/data/storyboard.json"))
os.makedirs(f"{ROOT}/public/shots",exist_ok=True)
TAIL=0.5
GRADE="eq=contrast=1.06:saturation=1.07:gamma=0.98,unsharp=5:5:0.4"
def vf(mode):
    if mode=="fill":
        return f"scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,{GRADE}"
    if mode.startswith("crop:"):
        x,y,w,h=map(float,mode[5:].split(","))
        return f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,{GRADE}"
    pre=""
    if mode.startswith("cropblur:"):
        x,y,w,h=map(float,mode[9:].split(",")); pre=f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"
    return (f"{pre}split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=30:3,eq=brightness=-0.12:saturation=0.8[bg];"
            f"[b]scale=-2:1080:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:0,{GRADE}")
def job(s):
    if s["src"]=="GFX": return s["id"],"gfx"
    out=f"{ROOT}/public/shots/{s['id']}.mp4"
    if os.path.exists(out) and '--force' not in sys.argv: return s["id"],"skip"
    dur=s["end"]-s["start"]+TAIL
    src=f"{ROOT}/public/{s['file']}"
    f=vf(s["mode"])+f",fps=30,setsar=1,tpad=stop_mode=clone:stop_duration={dur:.2f},trim=duration={dur:.3f},format=yuv420p"
    cmd=["ffmpeg","-y","-loglevel","error","-ss",str(s["ss"]),"-i",src,"-t",f"{dur+0.5:.3f}","-filter_complex" if ";" in f else "-vf",f,
         "-an","-c:v","libx264","-preset","medium","-crf","17","-g","30","-movflags","+faststart",out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    return s["id"], ("ok" if r.returncode==0 else "ERR "+r.stderr[-300:])
with ThreadPoolExecutor(4) as ex:
    for sid,st in ex.map(job,sb["shots"]): 
        if st not in("ok","skip","gfx"): print(sid,st)
print("done")
