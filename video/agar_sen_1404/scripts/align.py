# Align correct script words to whisper word timestamps via char-level sequence matching.
import json, re, difflib, unicodedata
W = json.load(open("/opt/work/tr/words.json"))
text = open("/opt/work/script/text.txt").read()
MAP = {"ş":"sh","ç":"ch","ğ":"g","ı":"i","ə":"a","ü":"u","ö":"o","x":"h","q":"k","w":"v","c":"j"}
def norm(s):
    s = s.lower()
    s = "".join(MAP.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s.replace("o","a").replace("e","a").replace("u","a").replace("i","a")
wc, wt = [], []
for seg in W:
    for w in seg["words"]:
        n = norm(w["w"])
        for k, ch in enumerate(n):
            wc.append(ch); wt.append(w["s"] + (w["e"]-w["s"]) * (k+.5)/max(1,len(n)))
tokens = [(m.group(), m.start()) for m in re.finditer(r"\S+", text)]
oc, own = [], []
for i, (tok, _) in enumerate(tokens):
    n = norm(tok)
    for ch in n: oc.append(ch); own.append(i)
sm = difflib.SequenceMatcher(None, "".join(oc), "".join(wc), autojunk=False)
ct = [None]*len(oc)
for a, b, size in sm.get_matching_blocks():
    for k in range(size): ct[a+k] = wt[b+k]
# interpolate missing char times
idx = [i for i, v in enumerate(ct) if v is not None]
import bisect
for i in range(len(ct)):
    if ct[i] is None:
        j = bisect.bisect(idx, i)
        lo = idx[j-1] if j > 0 else None; hi = idx[j] if j < len(idx) else None
        if lo is None: ct[i] = ct[hi]
        elif hi is None: ct[i] = ct[lo]
        else: ct[i] = ct[lo] + (ct[hi]-ct[lo])*(i-lo)/(hi-lo)
words = []
for i, (tok, pos) in enumerate(tokens):
    ts = [ct[k] for k in range(len(oc)) if own[k] == i]
    words.append({"w": tok, "pos": pos, "s": min(ts) if ts else None, "e": max(ts) if ts else None})
for i, w in enumerate(words):  # fill tokens without letters (e.g. "—")
    if w["s"] is None: w["s"] = w["e"] = words[i-1]["e"]
# word starts: shift a little earlier since char times are centers
for w in words: w["s"] = max(0, w["s"] - 0.12); w["e"] += 0.1
json.dump(words, open("/opt/work/script/aligned.json", "w"), ensure_ascii=False, indent=0)
print(sm.ratio(), len(words))
for w in words[::25]: print(f'{w["s"]:7.2f} {w["w"]}')
