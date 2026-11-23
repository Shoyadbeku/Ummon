# Tojikiston va XJS — yangiliklar reportaji (montaj loyihasi)

Bu papkada loyiha fayllari bor. Ular orqali videoni qayta tahrirlash va qayta render qilish mumkin.

| Fayl | Nima uchun |
|---|---|
| `transkript.md` | Audio matni, imlosi tuzatilgan va timecode bilan |
| `storyboard_timecode.md` | Har bir sahna: vaqti, fon kadri, manbasi, ekrandagi yozuvlar |
| `manbalar_va_litsenziyalar.md` | Barcha video, foto va faktlarning havolalari hamda litsenziyalari |
| `youtube_tavsif.txt` | YouTube description: bo‘limlar, manbalar, creditlar |
| `render/storyboard.js` | **Tahrirlanadigan montaj fayli.** Sahna vaqtlari, kadrlar va yozuvlar shu yerda |
| `render/engine.js` | Render dvigateli: Ken Burns, xaritalar, lower third, ticker, manba yozuvlari |
| `render/clips.json` | Har bir videolavha qaysi fayldan va qaysi soniyadan olingani |
| `render/audio.py` | Original fon musiqasi va effektlar sintezi |

## Qayta render qilish

1. Manba videolarni yuklab oling (havolalar `manbalar_va_litsenziyalar.md`da). So‘ng kadrlarga ajrating:
   `python3 render/extract.py <media/video> <frames>`
2. Web papka tuzing. Unda quyidagilar bo‘lsin:
   - `frames/` — kadrlar;
   - `photos/` — Kremlin fotolari;
   - `assets/` — `world.json` va Oswald shrifti;
   - `render/` papkasidagi fayllar.
3. Videoni render qiling:
   `node render/render.js <web_papka> video out.mp4 4`
4. Audioni tayyorlang:
   `python3 render/audio.py <out>`
   So‘ng ffmpeg bilan ovozni tozalang va miks qiling. Kerakli buyruqlar sessiya hisobotida bor.

Ekrandagi matnni yoki sahna vaqtini o‘zgartirish uchun `storyboard.js`ni tahrirlang va 3-qadamni qayta bajaring.
