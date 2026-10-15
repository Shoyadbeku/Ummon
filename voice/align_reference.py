"""Replace ASR transcripts of sequential segments with the matching span of a known reference text."""
import difflib
import json
import sys

from uzbek_text import normalize_cyr

asr_json, ref_txt, prefix = sys.argv[1:4]
ref = normalize_cyr(open(ref_txt).read()).split()
segs = [s for s in json.load(open(asr_json)) if prefix in s["wav"]]
pos = 0
for s in segs:
    hyp = normalize_cyr(s["text"])
    L = max(1, len(hyp.split()))
    best = (0.0, pos, pos)
    for i in range(max(0, pos - 3), min(len(ref), pos + 30)):
        for n in range(max(1, int(L * 0.6)), int(L * 1.6) + 2):
            r = difflib.SequenceMatcher(None, hyp, " ".join(ref[i:i + n])).ratio()
            if r > best[0]:
                best = (r, i, i + n)
    score, i, j = best
    s["ref"] = " ".join(ref[i:j])
    s["score"] = round(score, 3)
    if score > 0.5:
        pos = j
    print(f"{score:.2f} | {hyp}\n     | {s['ref']}", flush=True)
json.dump(segs, open(asr_json.replace(".json", f"_{prefix}_aligned.json"), "w"), ensure_ascii=False, indent=1)
