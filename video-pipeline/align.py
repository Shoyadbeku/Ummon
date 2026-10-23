# Align script words to ASR word timestamps -> scene times + subtitle lines
import json, re, sys, difflib, os
sys.path.insert(0, os.path.dirname(__file__))
from scenes import SCENES
asr = json.load(open(sys.argv[1])); total = float(sys.argv[2]); out = sys.argv[3]
def norm(w):
    w = w.lower().replace("‘", "'").replace("’", "'").replace("ʻ", "'").replace("ʼ", "'")
    w = w.replace("ç", "ch").replace("ş", "sh").replace("ğ", "g'").replace("ü", "u").replace("ı", "i").replace("ö", "o")
    w = re.sub(r"[^a-z0-9']", "", w).replace("'", "")
    return w.replace("q", "k").replace("x", "h").replace("o", "a")
script = []  # (scene, word)
for si, s in enumerate(SCENES):
    for w in s[0].split():
        script.append((si, w))
A = [norm(a["w"]) for a in asr]; S = [norm(w) for _, w in script]
# fuzzy token matching: DP-free approach using SequenceMatcher on tokens, then refine by similarity
sm = difflib.SequenceMatcher(None, S, A, autojunk=False)
times = [None] * len(S)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1): times[i1 + k] = (asr[j1 + k]["s"], asr[j1 + k]["e"])
    elif tag == "replace":
        # spread the script words over the ASR words proportionally
        n, m = i2 - i1, j2 - j1
        s0, e0 = asr[j1]["s"], asr[j2 - 1]["e"]
        for k in range(n):
            a = s0 + (e0 - s0) * k / n; b = s0 + (e0 - s0) * (k + 1) / n
            times[i1 + k] = (a, b)
matched = sum(1 for t in times if t); print("anchored", matched, "/", len(S))
# interpolate gaps
idx = [i for i, t in enumerate(times) if t]
for i in range(len(times)):
    if times[i] is None:
        prev = max([j for j in idx if j < i], default=None); nxt = min([j for j in idx if j > i], default=None)
        a = times[prev][1] if prev is not None else 0.0
        b = times[nxt][0] if nxt is not None else total
        lo = prev if prev is not None else -1; hi = nxt if nxt is not None else len(times)
        n, k = hi - lo - 1, i - lo - 1  # spread the run of unmatched words evenly over the gap
        times[i] = (a + (b - a) * k / n, a + (b - a) * (k + 1) / n)
# monotonic fix
for i in range(1, len(times)):
    s, e = times[i]
    if s < times[i - 1][0]: s = times[i - 1][0]
    times[i] = (s, max(e, s + 0.05))
words = [{"s": round(t[0], 3), "e": round(t[1], 3), "w": w, "sc": si} for (si, w), t in zip(script, times)]
# scenes: start = first word start - 0.25 (scene 0 at 0); end = next start
starts = []
for si in range(len(SCENES)):
    ws = [w for w in words if w["sc"] == si]
    starts.append(0.0 if si == 0 else max(0, ws[0]["s"] - 0.3))
scenes = []
for si, s in enumerate(SCENES):
    end = starts[si + 1] if si + 1 < len(SCENES) else total
    scenes.append({"start": round(starts[si], 3), "end": round(end, 3), "img": f"imgs/{si:02d}.jpg", "hook": s[2]})
# subtitle lines: chunks of up to 6 words, broken at punctuation / pauses
lines = []; cur = []
for k, w in enumerate(words):
    cur.append(w)
    nxt = words[k + 1] if k + 1 < len(words) else None
    brk = (len(cur) >= 6 or re.search(r"[.!?:;,]\"?$", w["w"]) and len(cur) >= 3 or re.search(r"[.!?]\"?$", w["w"])
           or nxt is None or nxt["sc"] != w["sc"] or (nxt and nxt["s"] - w["e"] > 0.6))
    if brk:
        lines.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": [{"s": x["s"], "e": x["e"], "w": x["w"]} for x in cur]}); cur = []
json.dump({"durationSec": total, "scenes": scenes, "lines": lines}, open(out, "w"), ensure_ascii=False, indent=1)
for s in scenes: print(f'{s["start"]:7.2f} {s["img"]} {s["hook"] or ""}')
