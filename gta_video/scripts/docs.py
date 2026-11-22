"""Generates deliverables/Storyboard.md and deliverables/Media_Sources.md from the project data."""
import json, re, sys
sb = open('src/storyboard.tsx', encoding='utf8').read()
words = json.load(open('src/data/words.json'))
rows = []
for line in sb.splitlines():
    m = re.search(r"\{t: ([\d.]+),", line)
    if not m: continue
    t = float(m.group(1))
    media = re.findall(r"v\('(\w+)'", line) + re.findall(r"im\('([\w.]+)'", line) + re.findall(r"img/([\w.]+)", line)
    comp = re.findall(r"<(PixelCity|LogoCard|Split|IconGrid|TimedList|Panels|HackUI|TrailerUI|DateShift|Platforms|TimelineRecap|Poll|BigWord|MapScene|Counter|YearStamp|Chapter|Quote|Kinetic)", line)
    comp += ['Kinetic'] * len(re.findall(r"\bK\(\[", line)) + ['Callout'] * len(re.findall(r"\bCO\(", line))
    texts = re.findall(r"(?:K\(\[|lines=\{\[)([^\]]*)\]", line)
    texts = [re.sub(r"[*']", '', x).replace(', ', ' / ') for x in texts]
    texts += [re.sub("'", '', x) for x in re.findall(r"CO\('([^']*)'", line)]
    texts += re.findall(r"(?:title|text|name|label|sub)[=:] ?[\"']([^\"']+)[\"']", line)[:6]
    fx = re.search(r"fx: '(\w+)'", line); sfx = re.search(r"sfx: \[([^\]]*)\]", line)
    rows.append([t, media, sorted(set(comp)), texts, fx.group(1) if fx else '', re.sub("'", '', sfx.group(1)) if sfx else ''])
END = 709.06
def ts(x): return f"{int(x//60):02}:{x%60:05.2f}"
out = ['# Storyboard — GTA tarixi (9:16, 30 fps, 11:49)\n', 'Har bir sahna ovozdagi aniq so‘z vaqtiga bog‘langan. Manba kodi: `src/storyboard.tsx`.\n',
       '| # | Vaqt | Ovoz (so‘zma-so‘z) | Vizual (fon) | Motion graphics / matn | Transition | SFX |', '|---|---|---|---|---|---|---|']
for i, r in enumerate(rows):
    t0 = r[0]; t1 = rows[i + 1][0] if i + 1 < len(rows) else END
    said = ' '.join(w['w'] for w in words if t0 <= w['s'] < t1)
    out.append(f"| {i+1} | {ts(t0)}–{ts(t1)} | {said} | {', '.join(r[1]) or 'grafik fon'} | {', '.join(r[2])}: {' · '.join(dict.fromkeys(r[3]))} | {r[4]} | {r[5]} |")
open('deliverables/Storyboard.md', 'w', encoding='utf8').write('\n'.join(out) + '\n')
# usage counts of clips
used = {}
for r in rows:
    for m in r[1]: used[m] = used.get(m, 0) + 1
json.dump(used, open('deliverables/_usage.json', 'w'), indent=0)
print(len(rows), 'scenes;', len(used), 'distinct media;', 'max reuse', max(used.values()))
