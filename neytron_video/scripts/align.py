"""Align the hand-corrected Uzbek transcript to Whisper word timings.
Usage: python3 align.py asr.json transcript_uz.txt out_dir"""
import json, sys, re, bisect
asr = json.load(open(sys.argv[1]))
lines = [l.strip() for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
out = sys.argv[3]
assert len(asr) == len(lines), (len(asr), len(lines))

def interp_builder(words, s0, s1):
    ws = [w for w in words if w["w"].strip()]
    if not ws:
        return lambda f: s0 + f * (s1 - s0)
    lens = [max(1, len(w["w"].strip())) for w in ws]
    tot = sum(lens); xs = []; ts = []; c = 0
    for w, L in zip(ws, lens):
        xs += [c / tot, (c + L) / tot]; ts += [w["s"], w["e"]]; c += L
    def f(x):
        if x <= 0: return ts[0]
        if x >= 1: return ts[-1]
        i = bisect.bisect_right(xs, x) - 1
        i = min(i, len(xs) - 2)
        x0, x1, t0, t1 = xs[i], xs[i + 1], ts[i], ts[i + 1]
        return t0 if x1 == x0 else t0 + (x - x0) / (x1 - x0) * (t1 - t0)
    return f

words = []; segs = []
for si, (seg, text) in enumerate(zip(asr, lines)):
    toks = text.split()
    f = interp_builder(seg["words"], seg["start"], seg["end"])
    lens = [len(re.sub(r"[^\w']", "", t)) or 1 for t in toks]
    tot = sum(lens); c = 0; sw = []
    for t, L in zip(toks, lens):
        s = f(c / tot); e = f((c + L) / tot); c += L
        sw.append({"t": t, "s": round(s, 3), "e": round(max(e, s + 0.08), 3), "seg": si})
    words += sw
    segs.append({"i": si, "s": sw[0]["s"], "e": sw[-1]["e"], "text": text})

json.dump({"words": words, "segments": segs}, open(f"{out}/timeline.json", "w"), ensure_ascii=False, indent=0)

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02}:{m:02}:{int(s):02},{int(round((s % 1) * 1000)) % 1000:03}"
# SRT: chunk each segment into <= 7 words / <= 42 chars lines
n = 1; srt = []
for seg in segs:
    sw = [w for w in words if w["seg"] == seg["i"]]
    chunk = []
    for w in sw:
        chunk.append(w)
        txt = " ".join(x["t"] for x in chunk)
        if len(chunk) >= 7 or len(txt) > 38 or w["t"][-1] in ".?!" or (w["t"][-1] in ",:—" and len(chunk) >= 3) or w is sw[-1]:
            srt.append(f"{n}\n{ts(chunk[0]['s'])} --> {ts(chunk[-1]['e'])}\n{txt}\n"); n += 1; chunk = []
open(f"{out}/Subtitles.srt", "w", encoding="utf-8").write("\n".join(srt))
print(len(words), "words,", n - 1, "srt cues")
