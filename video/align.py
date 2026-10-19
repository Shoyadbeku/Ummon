"""Matndagi har bir so'zni ovozdagi vaqtga moslaydi (ASR modelisiz, CPU'da).

Ovozdagi pauzalar (ffmpeg silencedetect) matndagi tinish belgilariga
dinamik dasturlash bilan bog'lanadi, oraliqdagi so'zlar esa harf soniga
qarab taqsimlanadi. Natija: words.json  [{"w": so'z, "s": boshi, "e": oxiri}]
"""
import json, math, re, subprocess, sys

audio, text_path, out = sys.argv[1], sys.argv[2], sys.argv[3]

log = subprocess.run(
    ["ffmpeg", "-v", "info", "-i", audio, "-af", "silencedetect=noise=-32dB:d=0.13", "-f", "null", "-"],
    capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                           capture_output=True, text=True).stdout)
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
speech_start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
speech_end = sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur
inner = [(a, b) for a, b in sil if a > speech_start + 0.05 and b < speech_end - 0.05]

words = open(text_path, encoding="utf-8").read().split()
weight = [len(re.sub(r"[^\w']", "", w)) + 2 for w in words]   # +2: har so'z orasidagi bo'g'in
brk_w = {".": 3.0, "?": 3.0, "!": 3.0, ",": 1.2, "—": 1.5, ":": 1.5, ";": 1.5}

def brk(w):
    t = w.rstrip("'\"")
    return brk_w.get(t[-1], 0) if t else 0

# so'zlardan keyingi kutilgan vaqtni hisoblash (harf tezligi bo'yicha)
total = sum(weight)
speech = speech_end - speech_start - sum(b - a for a, b in inner)
rate = speech / total
cum, c = [], 0
for w in weight:
    c += w
    cum.append(c)
breaks = [i for i, w in enumerate(words[:-1]) if brk(w) > 0]

def expected_time(i, assigned):
    # kutilgan vaqt = so'z pozitsiyasi + undan oldingi tanlangan pauzalar
    return speech_start + cum[i] * rate + assigned

# DP: pauza j -> break k (monoton). Moslanmagan pauza jarimasi.
J, K = len(inner), len(breaks)
INF = 1e18
dp = [[INF] * (K + 1) for _ in range(J + 1)]
bk = [[None] * (K + 1) for _ in range(J + 1)]
for k in range(K + 1):
    dp[0][k] = 0
prefix_sil = [0]
for a, b in inner:
    prefix_sil.append(prefix_sil[-1] + b - a)
for j in range(1, J + 1):
    a, b = inner[j - 1]
    for k in range(K + 1):
        # pauzani tashlab ketish (masalan nafas)
        best, arg = dp[j - 1][k] + 4.0 * (b - a) + 0.5, (j - 1, k, None)
        if k > 0:
            i = breaks[k - 1]
            t = expected_time(i, prefix_sil[j - 1])
            for kk in range(k):
                if dp[j - 1][kk] < INF:
                    # segment ichidagi gapirish tezligi me'yordan juda farq qilmasin
                    c0 = cum[breaks[kk - 1]] if kk > 0 else 0
                    t_prev = inner[j - 2][1] if j > 1 else speech_start
                    ratio = max(a - t_prev, 0.05) / max((cum[i] - c0) * rate, 0.05)
                    cost = (dp[j - 1][kk] + (t - a) ** 2 / 4 - 0.6 * brk(words[i])
                            + 3.0 * math.log(ratio) ** 2)
                    if cost < best:
                        best, arg = cost, (j - 1, kk, i)
        dp[j][k], bk[j][k] = best, arg
k = min(range(K + 1), key=lambda k: dp[J][k])
anchors, j = [], J
while j > 0:
    pj, pk, i = bk[j][k]
    if i is not None:
        anchors.append((i, inner[j - 1]))
    j, k = pj, pk
anchors.reverse()

# segmentlar: anchor so'zigacha gapirish, keyin pauza
res, start_i, t0 = [], 0, speech_start
for i, (a, b) in anchors + [(len(words) - 1, (speech_end, speech_end))]:
    seg = range(start_i, i + 1)
    tot = sum(weight[x] for x in seg)
    t = t0
    for x in seg:
        d = (a - t0) * weight[x] / tot
        res.append({"w": words[x], "s": round(t, 3), "e": round(t + d, 3)})
        t += d
    start_i, t0 = i + 1, b

json.dump({"duration": dur, "words": res, "pauses": [list(p) for p in inner],
           "anchors": [words[i] for i, _ in anchors]}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(res)} so'z, {len(anchors)}/{len(inner)} pauza moslandi; nutq {speech_start:.2f}-{speech_end:.2f}s")
