"""Asset preparation: cut, reframe to 9:16, unify colour grade and conform to 30 fps.

usage: python3 prep_assets.py <storyboard.json> <raw_dir> <public_dir>
raw_dir must contain  mixkit/<id>.mp4, wm/<key>.webm|jpg|png
Writes public/shots/<shot>.mp4, public/images/<key>.jpg and public/timeline.json
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sb_path, RAW, PUB = sys.argv[1:4]
sb = json.load(open(sb_path))
FPS = sb['fps']
TAIL = 0.7          # extra seconds so the next shot can dissolve over this one
W, H = 1080, 1920
os.makedirs(f'{PUB}/shots', exist_ok=True)
os.makedirs(f'{PUB}/images', exist_ok=True)

# One unified "premium Islamic documentary" grade: deep blacks, warm golden highlights,
# a hint of emerald in the shadows, slightly restrained saturation.
GRADE = ("eq=contrast=1.07:saturation=0.9:gamma=0.98,"
         "colorbalance=rs=-0.035:gs=0.02:bs=0.005:rm=0.01:gm=0.0:bm=-0.02:rh=0.055:gh=0.028:bh=-0.055,"
         "curves=master='0/0.015 0.12/0.085 0.5/0.5 0.85/0.885 1/0.975'")

def src_path(src):
    kind, key = src.split(':', 1)
    if kind == 'mk':
        return f'{RAW}/mixkit/{key}.mp4'
    if kind == 'wm':
        return f'{RAW}/wm/{key}.webm'
    if kind == 'img':
        for ext in ('jpg', 'jpeg', 'png', 'tif'):
            p = f'{RAW}/wm/{key}.{ext}'
            if os.path.exists(p):
                return p
        return f'{RAW}/wm/{key}.jpg'
    return None

def ok(p):
    return p and os.path.exists(p) and os.path.getsize(p) > 10000

def resolve(shot):
    src, at = shot['src'], shot['at']
    seen = 0
    while not src.startswith('gfx:') and not ok(src_path(src)) and seen < 4:
        fb = sb['fallback'].get(src)
        if fb is None:
            raise SystemExit(f'missing asset {src} and no fallback')
        if isinstance(fb, list):
            src, at = fb
        else:
            src = fb
        seen += 1
    return src, at

def probe(p):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height:format=duration', '-of', 'json', p], capture_output=True, text=True).stdout
    j = json.loads(o)
    return j['streams'][0]['width'], j['streams'][0]['height'], float(j['format']['duration'])

def prep_video(shot, src, at):
    out = f"{PUB}/shots/{shot['id']}.mp4"
    sig = json.dumps([src, at, shot['start'], shot['end'], shot['cx'], shot['sp'], GRADE])
    sigf = f"{PUB}/shots/.{shot['id']}.sig"
    if os.path.exists(out) and os.path.exists(sigf) and open(sigf).read() == sig:
        return out + ' (cached)'
    need = shot['end'] - shot['start'] + TAIL
    p = src_path(src)
    w, h, L = probe(p)
    sp = shot['sp']
    # make sure the source covers the required time; slow down (or start earlier) if needed
    if (L - at - 0.1) * (1 / sp) < need:
        at = max(0.0, L - 0.1 - need * sp)
    if (L - at - 0.1) / sp < need:
        at = 0.0
        sp = max(0.4, (L - 0.15) / need)
    hold = max(0.0, need - (L - at - 0.1) / sp)
    if w >= h:
        sw = int(round(w * H / h / 2) * 2)
        x = int((sw - W) * shot['cx'])
        geo = f"scale={sw}:{H}:flags=lanczos,crop={W}:{H}:{x}:0"
    else:
        geo = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    vf = f"setpts=(PTS-STARTPTS)/{sp},fps={FPS},{geo},unsharp=5:5:0.45,{GRADE}"
    if hold > 0:
        vf += f",tpad=stop_mode=clone:stop_duration={hold + 0.1:.2f}"
    # first -t limits input read, second -t limits output duration
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{at:.3f}', '-t', f'{need * sp + 0.3:.3f}', '-i', p,
           '-vf', vf, '-t', f'{need:.3f}', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
           '-pix_fmt', 'yuv420p', '-g', '15', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    open(sigf, 'w').write(sig)
    return out

def prep_image(key):
    p = src_path(f'img:{key}')
    out = f'{PUB}/images/{key}.jpg'
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', p, '-vf',
                        f"scale='min(2400,iw)':-2:flags=lanczos,{GRADE}", '-q:v', '2', out], check=True)
    return out

timeline = []
jobs = []
images = set()
for shot in sb['shots']:
    src, at = resolve(shot)
    t = dict(shot)
    t['src'] = src
    if src.startswith('mk:') or src.startswith('wm:'):
        t['kind'] = 'video'
        t['file'] = f"shots/{shot['id']}.mp4"
        jobs.append((shot, src, at))
    elif src.startswith('img:'):
        t['kind'] = 'image'
        key = src.split(':', 1)[1]
        t['file'] = f'images/{key}.jpg'
        images.add(key)
    else:
        t['kind'] = 'gfx'
        t['file'] = None
    timeline.append(t)

for k in images:
    prep_image(k)
with ThreadPoolExecutor(4) as ex:
    for f in ex.map(lambda j: prep_video(*j), jobs):
        print('ok', f, flush=True)

json.dump(dict(duration=sb['duration'], fps=FPS, tail=TAIL, shots=timeline),
          open(f'{PUB}/../src/timeline.json', 'w'), ensure_ascii=False, indent=1)
print('timeline written', len(timeline))
