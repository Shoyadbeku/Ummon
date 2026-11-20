import re, glob, os, subprocess, sys, concurrent.futures as cf
html_dirs = sys.argv[1:3]; out = sys.argv[3]; ids = sys.argv[4].split(',')
slug = {}
for d in html_dirs:
    for f in glob.glob(d + '/*.html'):
        for m in re.finditer(r'/free-stock-video/([a-z0-9-]+-(\d+))/', open(f, errors='ignore').read()):
            slug[m.group(2)] = m.group(1)
def run(i):
    dst = f"{out}/{i}.mp4"
    if os.path.exists(dst) and os.path.getsize(dst) > 100000: return i, 'have'
    for q in ('1080', '720'):
        if subprocess.run(['curl', '-sfL', '-m', '180', '-o', dst, f'https://assets.mixkit.co/videos/{i}/{i}-{q}.mp4']).returncode == 0: return i, q
    if i in slug:
        page = subprocess.run(['curl', '-s', '-m', '30', f'https://mixkit.co/free-stock-video/{slug[i]}/'], capture_output=True, text=True).stdout
        urls = sorted(set(re.findall(r'https://[^"]+-video-(?:1080|720)\.mp4', page)))
        urls.sort(key=lambda u: '1080' not in u)
        if urls and subprocess.run(['curl', '-sfL', '-m', '180', '-o', dst, urls[0]]).returncode == 0: return i, 'page'
    return i, 'FAIL'
with cf.ThreadPoolExecutor(10) as ex:
    for i, r in ex.map(run, ids): print(i, slug.get(i, '?')[:50], r)
