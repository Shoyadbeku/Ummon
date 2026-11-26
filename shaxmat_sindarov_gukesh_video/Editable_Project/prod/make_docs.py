"""Generate Storyboard.csv and Authentic_Media_Sources.csv directly from the render timeline."""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R

OUT = sys.argv[1]
SCR = R.SCR
titles = {}
for l in open(os.path.join(SCR, "imglist.txt")):
    if "|" in l:
        k, n = [x.strip() for x in l.split("|", 1)]
        if k and n: titles[k] = n
LIC_URL = {"CC0": "https://creativecommons.org/publicdomain/zero/1.0/", "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
           "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/", "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
           "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/", "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/"}

def fmt(t):
    m, s = divmod(t, 60); return f"{int(m):02}:{s:05.2f}"

segs = R.TR; lines = [l.strip() for l in open(os.path.join(SCR, "corrected.txt")) if l.strip()]

# record on-screen text by wrapping draw_text / d.text
captured = []
_orig = R.draw_text
def rec(d, xy, s, *a, **k):
    if k.get("alpha", 1.0) > 0.05 and s.strip(): captured.append(s)
    return _orig(d, xy, s, *a, **k)
R.draw_text = rec

R.frame(0.0)  # builds SHOTS
shots = R.SHOTS
rows = []
usage = {}
for i, sh in enumerate(shots):
    captured.clear()
    seen = []
    for tt in [sh.t0 + (sh.t1 - sh.t0) * f for f in (0.35, 0.7, 0.97)]:
        lay = R.Image.new("RGBA", (R.W, R.H)); d = R.ImageDraw.Draw(lay)
        for e in sh.els:
            if e.t0 <= tt <= e.t1: e.fn(d, tt)
        for c in captured:
            if c not in seen: seen.append(c)
        captured.clear()
    narr = " ".join(lines[j] for j, s in enumerate(segs) if s["start"] < sh.t1 - 0.05 and s["end"] > sh.t0 + 0.05)
    key = getattr(sh.bg, "key", None)
    for kk in (getattr(sh.bg, "keys", None) or []):
        usage.setdefault(kk, []).append(f"{fmt(sh.t0)}–{fmt(sh.t1)} (split-screen)")
    is_photo = key and sh.bg.__qualname__.startswith("P.")
    if key:
        usage.setdefault(key, []).append(f"{fmt(sh.t0)}–{fmt(sh.t1)}" + ("" if is_photo else " (xira fon)"))
    sk = getattr(sh.bg, "keys", None)
    visual = (("Split-screen fotolar: " + " | ".join(titles.get(x, x) for x in sk)) if sk else
              f"Foto (Ken Burns): {titles.get(key, key)}" if is_photo else
              (f"Motion graphics; fon: xiralashtirilgan foto ({titles.get(key, key)})" if key else "Motion graphics (to‘q ko‘k fon)"))
    rows.append({
        "scene": i + 1, "audio_start": fmt(sh.t0), "audio_end": fmt(min(sh.t1, R.AUDIO_END)) if sh.t0 < R.AUDIO_END else "—",
        "duration_s": round(sh.t1 - sh.t0, 2),
        "original_transcript": narr if sh.t0 < R.AUDIO_END else "(ovoz tugagan — yakuniy titrlar)",
        "visual": visual,
        "on_screen_text": " | ".join(seen)[:600],
        "footage_type": "Haqiqiy fotosurat (CC litsenziya)" if is_photo else "Grafika (faktlar asosida)",
        "source_url": f"https://commons.wikimedia.org/wiki/File:{titles[key].replace(' ', '_')}" if key in titles else "",
        "source_label_on_screen": sh.credit or "",
        "license_or_basis": (R.CREDITS.get(key, "").split("· ")[-1] if key else "Original grafika"),
        "transition_in": "Kesish (cut)" if sh.trans == "cut" or i == 0 else "Crossfade 0.4 s",
        "why_this_visual": "",
    })

why = {
 1: "Hook: ikki raqib yonma-yon (arxiv portretlar), '20' yoshi kinetik tipografiya, impact effekti; 'da’vogar'/'jahon chempioni' yorliqlari so‘z aytilgan lahzada",
 3: "Jeneva — Martin Bodmer jamg‘armasi hududidan haqiqiy ko‘l manzarasi",
 5: "Hisob tablosi: 2 partiyadan keyin 1—1",
}
for r in rows:
    r["why_this_visual"] = why.get(r["scene"], "Ovozdagi jumlani mos sana/raqam/joy grafikasi yoki tegishli joy surati bilan ko‘rsatish")

with open(os.path.join(OUT, "Storyboard.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# media sources
AUTH = {}
for k, c in R.CREDITS.items():
    part = c.split("FOTO: ")[-1]
    AUTH[k] = (part.split(" / ")[0], part.split("· ")[-1])
with open(os.path.join(OUT, "Authentic_Media_Sources.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "type", "title", "author", "license", "license_url", "source_page", "what_it_shows", "used_at_timecodes", "on_screen_label", "verification_note"])
    notes = {
        "sind_olymp45": "Javohir Sindarov, 45-Shaxmat olimpiadasi (Budapesht, 2024). Jeneva o‘yini EMAS — ekranda 'ARXIV' bilan.",
        "sind_46": "Sindarov, 46-Olimpiada (Samarqand, 2026). ARXIV.",
        "sind_tb": "Sindarov, Wikimedia Commons portreti. ARXIV.",
        "guk24": "Gukesh Dommaraju, 2024. ARXIV — Jeneva o‘yini EMAS.",
        "guk_cand1": "Gukesh, Nomzodlar turniri 2024 (Toronto). Singapur haqidagi kartochka ostida, lekin yorliq tadbirni aniq ko‘rsatadi.",
        "bodmer_view": "Martin Bodmer jamg‘armasi hududidan Jeneva ko‘liga ko‘rinish (2014).",
        "team44": "O‘zbekiston terma jamoasi, 44-Olimpiada (Chennay, 2022) — oltin medal jamoasi.",
        "team46": "O‘zbekiston 1-terma jamoasi, 46-Olimpiada (Samarqand, 2026).",
        "carlsen": "Magnus Karlsen, 2025 (tezkor va blits).",
    }
    for k, times in usage.items():
        a, lic = AUTH.get(k, ("", ""))
        w.writerow([k, "photo", titles.get(k, ""), a, lic, LIC_URL.get(lic, ""),
                    f"https://commons.wikimedia.org/wiki/File:{titles[k].replace(' ', '_')}" if k in titles else "",
                    R.CREDITS.get(k, "").split(" · FOTO")[0] if " · FOTO" in R.CREDITS.get(k, "") else "Oliy Majlis / bino",
                    "; ".join(times), R.CREDITS.get(k, ""), notes.get(k, "Joy va mazmun tekshirildi")])
    w.writerow(["map_world", "vector data", "countries.geo.json", "johan/world.geo.json (Natural Earth asosida)", "Unlicense / Public domain", "https://unlicense.org/",
                "https://github.com/johan/world.geo.json", "Jeneva (Kolonyi), Goa, Kipr belgilangan xaritalar", "00:31.6–00:38.6; 02:21.8–02:31.1; 02:37.8–02:46.6", "—", "Nuqtalar haqiqiy joylarda (Kolonyi 46.22N 6.18E; Goa 15.49N 73.83E; Pegeia 34.88N 32.39E)"])
    w.writerow(["chess_diagrams", "graphics", "Berlin himoyasi / London tizimi diagrammalari", "Original (FEN asosida chizilgan)", "Original", "", "", "1-partiya debyuti (1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6); London tizimi sxemasi (1.d4, 2.Bf4)", "01:08.5–01:22.7; 01:33.2–01:44.2", "—", "London diagrammasi — sxema, 2-partiyaning aniq pozitsiyasi emas (ekranda 'Sxema')"])
    w.writerow(["music", "audio", "Music bed + SFX", "Original (dasturiy sintez, ushbu loyiha)", "Original", "", "", "Fon musiqasi, whoosh, impact, tick", "butun video", "—", "Uchinchi tomon namunalari ishlatilmagan"])
    w.writerow(["voice", "audio", "Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 7.wav", "Muallif (foydalanuvchi)", "Muallifning o‘z ovozi", "", "iCloud Drive", "Asosiy diktor ovozi", "00:00–05:45.40", "—", "Fayl nomi mazmunga mos emas: audio Jahon shaxmat chempionati haqida"])
print(len(rows), "scenes;", len(usage), "photos used")
json.dump({k: v for k, v in usage.items()}, open(os.path.join(OUT, ".usage.json"), "w"), ensure_ascii=False, indent=1)
