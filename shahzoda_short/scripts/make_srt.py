"""Builds Subtitles.srt from the word timings in src/data/timing.ts (phrase-level cues, ≤ 44 chars)."""
import re, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / 'src/data/timing.ts').read_text(encoding='utf-8')
words = [(m[0], float(m[1]), float(m[2])) for m in re.findall(r"\{t: '([^']+)', s: ([\d.]+), e: ([\d.]+)", src)]
cues, cur = [], []
for w in words:
    if cur and (len(' '.join(x[0] for x in cur + [w])) > 44 or w[1] - cur[-1][2] > 0.35):
        cues.append(cur); cur = []
    cur.append(w)
    if re.search(r'[.?!]$', w[0]) or (w[0].endswith(',') and len(' '.join(x[0] for x in cur)) > 18):
        cues.append(cur); cur = []
if cur: cues.append(cur)
ts = lambda s: f"{int(s//3600):02}:{int(s%3600//60):02}:{int(s%60):02},{int(round(s%1*1000)):03}"
out = []
for i, c in enumerate(cues, 1):
    end = c[-1][2] + 0.15
    if i < len(cues): end = min(end, cues[i][0][1] - 0.02)
    out.append(f"{i}\n{ts(c[0][1])} --> {ts(end)}\n{' '.join(x[0] for x in c)}\n")
pathlib.Path(sys.argv[1]).write_text('\n'.join(out), encoding='utf-8')
print(len(cues), 'cues')
