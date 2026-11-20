"""Turn data/storyboard.py + data/timeline.json into src/shots.json (absolute times)."""
import json, sys, runpy, collections
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
S = runpy.run_path(f"{ROOT}/data/storyboard.py")["S"]
tl = json.load(open(f"{ROOT}/data/timeline.json"))
AUDIO_END = 614.47
segw = collections.defaultdict(list)
for w in tl["words"]: segw[w["seg"]].append(w)
def t(seg, wi): return segw[seg][wi]["s"]
shots = []
for k, (seg, wi, vis, ov) in enumerate(S):
    start = 0.0 if k == 0 else max(0, t(seg, wi) - 0.06)
    sh = {"start": round(start, 3), "seg": seg, "word": wi}
    if isinstance(vis, str):
        sh.update(kind="clip", clip=vis)
    else:
        _, name, props = vis
        props = dict(props)
        if "words" in props: props["times"] = [t(seg, x) for x in props.pop("words")]
        if "at" in props: props["times"] = [t(a, b) for a, b in props.pop("at")]
        if "stampWord" in props: props["stampTime"] = t(seg, props.pop("stampWord"))
        sh.update(kind="mg", mg=name, props=props)
    if ov: sh["overlay"] = {"type": ov[0], "text": ov[1], "extra": ov[2] if len(ov) > 2 else None}
    shots.append(sh)
for a, b in zip(shots, shots[1:]): a["end"] = b["start"]
shots[-1]["end"] = AUDIO_END
for s in shots: s["dur"] = round(s["end"] - s["start"], 3)
# collect clips
uses = collections.Counter()
for s in shots:
    if s["kind"] == "clip": uses[s["clip"]] += 1
    p = s.get("props", {})
    for c in [p.get("bg"), p.get("clipA"), p.get("clipB")] + p.get("clips", []):
        if c: uses[c] += 1
dups = {c: n for c, n in uses.items() if n > 1}
json.dump(shots, open(f"{ROOT}/src/shots.json", "w"), ensure_ascii=False, indent=1)
print(len(shots), "shots,", len(uses), "unique clips, dups:", dups)
print("min/max dur", min(s["dur"] for s in shots), max(s["dur"] for s in shots))
for s in sorted(shots, key=lambda s: s["dur"])[:5]: print("short", s["seg"], s["word"], s["dur"])
for s in sorted(shots, key=lambda s: -s["dur"])[:5]: print("long", s["seg"], s["word"], s["dur"], s.get("clip", s.get("mg")))
