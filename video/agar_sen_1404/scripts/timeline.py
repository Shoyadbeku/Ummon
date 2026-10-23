import json, re
words = json.load(open("/opt/work/script/aligned.json"))
scenes = json.load(open("/opt/work/script/scenes.json"))
text = open("/opt/work/script/text.txt").read()
HOOK = 6.5; AUDIO = 306.49; OUTRO = 4.0; TOTAL = HOOK + AUDIO + OUTRO
def t_at(pos):
    for w in words:
        if w["pos"] + len(w["w"]) > pos: return w["s"]
out = []
for i, s in enumerate(scenes):
    st = 0.0 if i == 0 else t_at(text.index(s["a"])) - 0.25
    out.append({"id": s["id"], "start": round(HOOK + st, 3)})
for i, s in enumerate(out):
    s["end"] = out[i+1]["start"] if i+1 < len(out) else TOTAL
# era by scene id
MODERN = {19, 25, 31, 32, 35, 41}
def era(n):
    if n in MODERN: return "now"
    if 37 <= n <= 47: return "1980"
    if 48 <= n <= 52: return "1950"
    if 10 <= n <= 36: return "1404"
    return "now"
for s in out: s["era"] = era(int(s["id"][1:]))
# subtitles: chunks ending at punctuation or ~6 words / 40 chars
subs, cur = [], []
for w in words:
    cur.append(w)
    txt = " ".join(x["w"] for x in cur)
    if re.search(r"[.,!?;:—]$", w["w"]) or w["w"] == "—" or len(cur) >= 7 or len(txt) > 42:
        subs.append(cur); cur = []
if cur: subs.append(cur)
S = []
for c in subs:
    c = [x for x in c if x["w"] != "—"] or c
    S.append({"start": round(HOOK + c[0]["s"], 3), "end": round(HOOK + c[-1]["e"] + 0.25, 3),
              "words": [{"w": x["w"], "s": round(HOOK + x["s"], 3)} for x in c]})
for i in range(len(S)-1): S[i]["end"] = min(S[i]["end"], S[i+1]["start"])
cards = [{"label": "SAMARQAND", "year": "1404", "start": t_at(text.index("1404-yilda Samarqandda")) + HOOK},
         {"label": "SSSR", "year": "1980", "start": t_at(text.index("1980-yilga burib")) + HOOK},
         {"label": "21 YOSH", "year": "1950", "start": t_at(text.index("1950-yilda")) + HOOK},
         {"label": "BUGUN", "year": "2026", "start": t_at(text.index("Bugun sizning")) + HOOK}]
json.dump({"fps": 30, "hook": HOOK, "total": TOTAL, "scenes": out, "subs": S, "cards": cards},
          open("/opt/work/rv/public/timeline.json", "w"), ensure_ascii=False, indent=1)
for s in out: print(s["id"], s["start"], round(s["end"]-s["start"], 2), s["era"])
print(cards); print(len(S), "subs")
