"""Forced alignment (torchaudio MMS_FA, wav2vec2 CTC) of the corrected transcript -> word timestamps.
usage: python align.py voice16k.wav transcript_corrected.json whisper_chunks_raw.json out_transcript.json"""
import sys, json, re, wave
import numpy as np, torch, torchaudio
from torchaudio.pipelines import MMS_FA as B

wav, corr, rawc, out = sys.argv[1:5]
w = wave.open(wav); sr = w.getframerate()
audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
C = json.load(open(corr)); raw = json.load(open(rawc))
model = B.get_model(with_star=False).eval(); tok = B.get_tokenizer(); aligner = B.get_aligner()

def romanize(s):
    s = s.lower().replace("ʻ", "'").replace("’", "'").replace("‘", "'").replace("ʼ", "'").replace("`", "'")
    s = re.sub(r"[^a-z']", "", s)
    s = s.strip("'")
    return s

def parse(text, ci):
    words = []
    # [spoken|display] groups
    parts = re.findall(r"\[[^\]]+\]|\S+", text)
    for p in parts:
        if p.startswith("["):
            spoken, disp = p[1:-1].split("|")
            sub = spoken.split()
            for j, sw in enumerate(sub):
                words.append({"text": disp if j == 0 else "", "spoken": sw, "dis": False, "chunk": ci, "merged": j > 0})
            continue
        dis = p.startswith("{dis}")
        p = p.replace("{dis}", "")
        words.append({"text": p, "spoken": p, "dis": dis, "chunk": ci, "merged": False})
    return words

allwords = []
for (a, b) in C["groups"]:
    s0, e0 = raw[a]["start"], raw[b]["end"]
    ws = []
    for ci in range(a, b + 1): ws += parse(C["chunks"][ci], ci)
    seg = torch.from_numpy(audio[int(s0 * sr):int(e0 * sr)]).unsqueeze(0)
    with torch.inference_mode():
        em, _ = model(seg)
    em = torch.log_softmax(em, -1)
    idx = [i for i, x in enumerate(ws) if romanize(x["spoken"])]
    toks = tok([romanize(ws[i]["spoken"]) for i in idx])
    spans = aligner(em[0], toks)
    ratio = seg.shape[1] / em.shape[1] / sr
    scores = []
    for k, i in enumerate(idx):
        sp = spans[k]
        ws[i]["start"] = round(s0 + sp[0].start * ratio, 3)
        ws[i]["end"] = round(s0 + sp[-1].end * ratio, 3)
        sc = float(np.mean([x.score for x in sp])); ws[i]["score"] = round(sc, 3); scores.append(sc)
    # punctuation-only tokens: attach to previous word time
    for i, x in enumerate(ws):
        if "start" not in x:
            x["start"] = ws[i-1]["end"] if i else s0; x["end"] = x["start"]; x["score"] = 1
    print(f"group {a}-{b} [{s0:.1f}-{e0:.1f}] words={len(ws)} meanScore={np.mean(scores):.3f} low={sum(s<0.25 for s in scores)}")
    allwords += ws

# merge [spoken|display] groups into one display word spanning all
words = []
for x in allwords:
    if x["merged"]: words[-1]["end"] = x["end"]; continue
    words.append(x)
for x in words: x.pop("merged", None); x.pop("spoken", None) if x["text"] == x["spoken"] else None
# sentences
sents = []; cur = []
for x in words:
    cur.append(x)
    if re.search(r"[.?!]»?$", x["text"]) : sents.append(cur); cur = []
if cur: sents.append(cur)
res = {"language": "uz", "audio": "voice.wav", "duration": round(len(audio) / sr, 3),
       "method": "faster-whisper (hostmepanda/whisper-large-v3-turbo-uzbek-ct2) transcription + manual ASR-error correction + torchaudio MMS_FA forced alignment",
       "sentences": [{"id": i, "start": s[0]["start"], "end": s[-1]["end"],
                      "text": " ".join(w["text"] for w in s if not w["dis"]), "words": s} for i, s in enumerate(sents)]}
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
print("sentences", len(sents), "words", len(words))
