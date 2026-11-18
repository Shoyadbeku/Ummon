"""Build Subtitles.srt from remotion/src/data/words.ts (phrase-level cues, max ~6 words)."""
import re, sys
src = open(sys.argv[1]).read()
words = [(m.group(1), float(m.group(2)), float(m.group(3))) for m in re.finditer(r"\{w: ['\"](.+?)['\"], s: ([\d.]+), e: ([\d.]+)", src)]
cues, cur = [], []
for i, (w, s, e) in enumerate(words):
    cur.append((w, s, e))
    nxt = words[i + 1] if i + 1 < len(words) else None
    if re.search(r"[.,?!]$", w) or len(cur) >= 6 or not nxt or nxt[1] - e > 0.3:
        cues.append(cur); cur = []
ts = lambda t: f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round((t%1)*1000)):03d}"
out = []
for i, c in enumerate(cues):
    out.append(f"{i+1}\n{ts(c[0][1])} --> {ts(c[-1][2])}\n{' '.join(x[0] for x in c)}\n")
open(sys.argv[2], "w").write("\n".join(out))
print(len(words), "words,", len(cues), "cues")
