import json, collections
shots = json.load(open("src/shots.json")); tl = json.load(open("data/timeline.json"))
segs = {s["i"]: s["text"] for s in tl["segments"]}
def ts(t): return f"{int(t//60):02}:{t%60:05.2f}"
def clips_of(s):
    if s["kind"] == "clip": return [s["clip"]]
    p = s["props"]; return [c for c in [p.get("bg"), p.get("clipA"), p.get("clipB")] + p.get("clips", []) if c]
L = ["# Storyboard — \"Dunyoni aslida kim boshqaradi?\"", "",
     "16:9 · 1920×1080 · 30 fps · 10:14.47 · 206 kadr (shot). Vaqtlar videodagi boshlanish vaqti.", "",
     "| # | Vaqt | Davom. | Ovozdagi gap | Vizual | Overlay / grafika |", "|---|---|---|---|---|---|"]
for i, s in enumerate(shots):
    vis = f"Footage `mixkit {s['clip'][2:]}`" if s["kind"] == "clip" else f"**MG: {s['mg']}**" + (f" (fon/klip: {', '.join('mixkit '+c[2:] for c in clips_of(s))})" if clips_of(s) else "")
    ov = s.get("overlay"); ovs = f"{ov['type']}: {ov['text']}" + (f" — {ov['extra']}" if ov and ov.get('extra') else "") if ov else ""
    if s["kind"] == "mg":
        p = s["props"]; ovs = " / ".join(str(x) for x in [p.get("title"), p.get("text"), ", ".join(p.get("items", []))] if x)
    txt = segs[s["seg"]] if s["word"] == 0 else "… " + " ".join(segs[s["seg"]].split()[s["word"]:])
    L.append(f"| {i+1} | {ts(s['start'])} | {s['dur']:.1f}s | {txt[:110]} | {vis} | {ovs} |")
open("Storyboard.md", "w").write("\n".join(L) + "\n")
use = collections.defaultdict(list)
for i, s in enumerate(shots):
    for c in clips_of(s): use[c[2:]].append(f"#{i+1} ({ts(s['start'])})")
M = ["# Media manbalari va litsenziyalar", "",
     "Barcha video lavhalar **Mixkit** (mixkit.co) saytidan olingan va **Mixkit Stock Video Free License** asosida tijoriy va notijoriy loyihalarda bepul, atribusiyasiz ishlatilishi mumkin (https://mixkit.co/license/#videoFree). Ijtimoiy tarmoqlardan (YouTube, X, Facebook va h.k.) mualliflik huquqi noaniq material **olinmadi**.",
     "", "Musiqa: **Mixkit Stock Music Free License** (https://mixkit.co/license/#musicFree). Ovoz effektlari: **Mixkit Sound Effects Free License** (https://mixkit.co/license/#sfxFree).",
     "", "Wikimedia Commons API ish vaqtida so'rovlarni cheklab qo'ydi (HTTP 429), Pexels/Pixabay API kalit talab qiladi — shuning uchun ulardan foydalanilmadi.",
     "", "Xarita: `world-atlas` (Natural Earth ma'lumotlari, public domain) + `d3-geo` (ISC).", "",
     "## Video lavhalar", "", "| Mixkit ID | Yuklab olingan fayl | Qayerda ishlatilgan |", "|---|---|---|"]
for cid in sorted(use, key=int):
    url = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4" if int(cid) < 100000 else f"https://mixkit.co/free-stock-video/download/{cid}/"
    M.append(f"| {cid} | {url} | {', '.join(use[cid])} |")
M += ["", "## Musiqa (bo'limlar bo'yicha)", "", "| Mixkit ID | Nomi | Vaqt oralig'i |", "|---|---|---|",
      "| 188 | Echoes | 00:00 – 01:35 (kirish, prezidentlar) |", "| 565 | Fallen (Asper) | 01:35 – 03:59 (banklar, eng katta pullar) |",
      "| 140 | Cyberpunk City | 03:59 – 05:22 (axborot) |", "| 73 | Torn Threads | 05:22 – 06:12 (energiya) |",
      "| 588 | Feedback Dreams | 06:12 – 08:11 (maxfiy guruhlar) |", "| 587 | Discover | 08:11 – 10:14 (xulosa) |", "",
      "Nomlar Mixkit katalog sahifasidan olingan; fayl manzili: `https://assets.mixkit.co/music/<ID>/<ID>.mp3`.", "",
      "## Ovoz effektlari", "", "| Mixkit SFX ID | Turi | Qayerda |", "|---|---|---|",
      "| 1279 | impact (bass hit) | hook |", "| 1491 | whoosh | hook, savol kartalari |", "| 1489 | long whoosh / riser | bo'lim kartalari |",
      "| 1143 | cinematic impact | bo'lim kartalari |", "| 2150 | short impact | muhr (stamp) va savollar |", "| 1485 | short whoosh | motion graphics kirishi |",
      "| 2357 | pop | label / stat chiplar |", "| 1031 | glitch | \"So'nggi xabar\" banneri |", "",
      "Manzil: `https://assets.mixkit.co/active_storage/sfx/<ID>/<ID>-preview.mp3`."]
open("Media_Sources.md", "w").write("\n".join(M) + "\n")
print("ok", len(use))
