# O‘zbekiston U-17 — Ispaniya: yangiliklar-reportaj montaji

Diktor ovozi asosida (5:10) tayyorlangan, YouTube uchun news-documentary uslubidagi montaj.

## Fayllar

| Fayl | Nima |
|---|---|
| `u17_ispaniya_preview.mp4` | Siqilgan nusxa (GitHub 100 MB chegarasi uchun). **Yuklash uchun to‘liq sifatli master nusxani alohida yuborildi.** |
| `storyboard.md` | 89 ta sahna: timecode, ovoz matni, kadr, manba va kirish nuqtasi, effekt |
| `manbalar.md` | Barcha video manbalar, havolalar, mualliflar, litsenziya holati, fakt manbalari |
| `youtube_tavsif.txt` | YouTube tavsifi: bo‘limlar (chapters), heshteglar, to‘liq creditlar |
| `subtitr_uz.srt` | Imlosi tuzatilgan o‘zbekcha subtitr (YouTube'ga alohida yuklanadi) |
| `loyiha/` | Tahrirlanadigan loyiha: montajni qayta yig‘adigan skriptlar |

## Texnik parametrlar (master)

- 1920×1080, 25 fps, H.264 High, AAC 320 kbps, −14 LUFS (YouTube normasi)
- 4K emas: barcha manba videolar 1080p (bittasi 720p). 4K ga cho‘zish sifat qo‘shmaydi, faqat fayl hajmini oshiradi.

## Loyihani qayta yig‘ish (`loyiha/`)

1. `dl.py <YouTube ID>` — SnapAny orqali videoni yuklaydi (`snapget.js` Playwright bilan)
2. `edl.py` — storyboard: sahnalar, manbalar, kirish nuqtalari (shu faylni tahrirlab kadrlarni almashtirish mumkin)
3. `render_base.py` — sahnalarni kesadi, rang korreksiyasi, pan/zoom, concat → `build/base.mp4`
4. `music.py` — original musiqa va SFX sintezi → `build/music.wav`, `build/sfx.wav`
5. `gfx.py` — barcha animatsion grafikalar (lower third, tablolar, jadval, manba yozuvlari); `preview.py <soniya…>` — namunaviy kadrlar
6. `final.sh` — grafika + video + audio miks → `build/final.mp4`

## Diqqat: audiodagi bitta faktik xato

**02:42–02:46** — "Birinchi bo‘lim ispanlar foydasiga 2:0 hisobida tugadi". ESPN ma’lumotiga ko‘ra birinchi bo‘lim **2:1** tugagan: Behruz Shukurullayev 45+4-daqiqada gol urgan, Amirbek Saidov 53-daqiqada hisobni tenglashtirgan. Ekrandagi grafika to‘g‘ri gollar vaqtini ko‘rsatadi. Shu jumlani qayta yozib, almashtirish tavsiya etiladi (masalan: "Ispanlar 2:0 hisobida oldinga o‘tdi, biznikilar tanaffusgacha bitta, ikkinchi bo‘limda yana bitta gol urdi").
