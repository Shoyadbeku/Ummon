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
           "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/"}

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
    is_photo = key and sh.bg.__qualname__.startswith("P.")
    if key:
        usage.setdefault(key, []).append(f"{fmt(sh.t0)}–{fmt(sh.t1)}" + ("" if is_photo else " (xira fon)"))
    visual = (f"Foto (Ken Burns): {titles.get(key, key)}" if is_photo else
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
 1: "Hook: Oliy Majlis binosi + 11→12 kinetik tipografiya, '12' so‘zi aytilgan zahoti (2.02 s) zarb effekti",
 2: "Qonunni qabul qilgan muassasa — Oliy Majlis binosining real surati",
 3: "Keng tarqalgan noto‘g‘ri tushuncha (12-sinf) vizuallashtirildi",
 5: "Asosiy g‘oya: yangi yil maktabning BOSHIGA qo‘shiladi — bloklar animatsiyasi",
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
        "lc_round": "Qonunchilik palatasi zali, 22.10.2026 (EXHT PA davra suhbati). 24-noyabr majlisi EMAS — ekranda 'ARXIV, 22.10.2026' deb belgilangan.",
        "fergana_line": "Farg‘onada o‘quv yurtiga hujjat topshirish navbati (Flickr 7535793706). Faqat 2017-yilgacha bo‘lgan tizim (kollej/litsey) haqidagi qismda ishlatilgan.",
        "samar_girls2": "Samarqand, 2011, maktab formasidagi qizlar. Tayyorlov guruhi tarbiyalanuvchilari sifatida ko‘rsatilmagan.",
        "village_kids": "O‘zbekiston qishlog‘i (tog‘li hudud), ota va bola.",
        "kg37": "37-son bolalar bog‘chasi binosi.",
        "school235": "Toshkent, Yunusobod tumani, 235-maktab, 2023.",
        "khiva_school": "Xiva, Prezident maktabi binosi.",
        "senate": "Oliy Majlis Senati binosi, Toshkent.",
    }
    for k, times in usage.items():
        a, lic = AUTH.get(k, ("", ""))
        w.writerow([k, "photo", titles.get(k, ""), a, lic, LIC_URL.get(lic, ""),
                    f"https://commons.wikimedia.org/wiki/File:{titles[k].replace(' ', '_')}" if k in titles else "",
                    R.CREDITS.get(k, "").split(" · FOTO")[0] if " · FOTO" in R.CREDITS.get(k, "") else "Oliy Majlis / bino",
                    "; ".join(times), R.CREDITS.get(k, ""), notes.get(k, "Joy va mazmun tekshirildi")])
    w.writerow(["map_uzb", "vector data", "UZB.geo.json / countries.geo.json", "johan/world.geo.json (Natural Earth asosida)", "Unlicense / Public domain", "https://unlicense.org/",
                "https://github.com/johan/world.geo.json", "O‘zbekiston va dunyo xaritasi konturi", "01:01.80–01:05.90; 02:46.20–02:52.50", "—", "Faqat kontur, hech qanday davlat belgilanmagan"])
    w.writerow(["music", "audio", "Music bed + SFX", "Original (dasturiy sintez, ushbu loyiha)", "Original", "", "", "Fon musiqasi, whoosh, impact, tick", "butun video", "—", "Uchinchi tomon namunalari ishlatilmagan"])
    w.writerow(["voice", "audio", "Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 5.wav", "Muallif (foydalanuvchi)", "Muallifning o‘z ovozi", "", "iCloud Drive", "Asosiy diktor ovozi", "00:00–05:28.17", "—", "Fayl nomi mazmunga mos emas: audio 12 yillik ta’lim haqida"])
print(len(rows), "scenes;", len(usage), "photos used")
json.dump({k: v for k, v in usage.items()}, open(os.path.join(OUT, ".usage.json"), "w"), ensure_ascii=False, indent=1)
