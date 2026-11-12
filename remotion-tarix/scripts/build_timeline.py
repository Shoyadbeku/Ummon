"""Whisper transkripti (so'z vaqtlari) + tuzatilgan matn -> src/data/subtitles.json, scenes.json
Ishlatish: python3 scripts/build_timeline.py transcript.json
"""
import json, sys, os, glob, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tr = json.load(open(sys.argv[1]))
lines = [l.strip() for l in open(os.path.join(root, 'scripts/narration.txt'), encoding='utf-8')]
assert len(lines) == len(tr), (len(lines), len(tr))

subs = []
for seg, text in zip(tr, lines):
    ww = [w for w in seg['words'] if w['w'].strip()] or [{'w': seg['text'], 's': seg['start'], 'e': seg['end']}]
    # whisper so'zlarining kumulyativ belgi ulushi -> vaqt
    tot = sum(len(w['w'].strip()) + 1 for w in ww)
    pts, acc = [], 0
    for w in ww:
        pts.append((acc / tot, w['s']))
        acc += len(w['w'].strip()) + 1
    pts.append((1.0, ww[-1]['e']))
    def at(f):
        for (f0, t0), (f1, t1) in zip(pts, pts[1:]):
            if f <= f1:
                return t0 + (t1 - t0) * ((f - f0) / (f1 - f0) if f1 > f0 else 0)
        return pts[-1][1]
    words = text.split()
    tot2 = sum(len(w) + 1 for w in words)
    out, acc = [], 0
    for w in words:
        out.append({'t': w, 's': round(at(acc / tot2), 3)})
        acc += len(w) + 1
    subs.append({'start': round(seg['start'], 3), 'end': round(seg['end'], 3), 'words': out})

imgs = {int(os.path.basename(p)[:2]): 'images/' + os.path.basename(p) for p in glob.glob(os.path.join(root, 'public/images/*.jpg'))}
mp = [tuple(map(int, l.split())) for l in open(os.path.join(root, 'scripts/scene_map.txt')) if l.strip() and not l.startswith('#')]
scenes, seen = [], set()
for k, (si, n) in enumerate(mp):
    start = 0.0 if k == 0 else subs[si]['start'] - 0.25
    end = (subs[mp[k + 1][0]]['start'] - 0.25) if k + 1 < len(mp) else subs[-1]['end']
    text = ' '.join(' '.join(w['t'] for w in s['words']) for s in subs[si:(mp[k + 1][0] if k + 1 < len(mp) else len(subs))])
    scenes.append({'n': n, 'repeat': n in seen, 'image': imgs[n], 'text': text, 'start': round(start, 3), 'end': round(end, 3), 'words': []})
    seen.add(n)
os.makedirs(os.path.join(root, 'src/data'), exist_ok=True)
json.dump(subs, open(os.path.join(root, 'src/data/subtitles.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(scenes, open(os.path.join(root, 'src/data/scenes.json'), 'w'), ensure_ascii=False, indent=1)
print(len(subs), 'subtitr,', len(scenes), 'sahna; ovoz oxiri', subs[-1]['end'])
