# Putin Dushanbeda: 201-baza va Markaziy Osiyo xavfsizligi

Muallif ovozi (6:15, WAV) asosida yigʻilgan yangiliklar-hujjatli reportaj.

| Fayl | Nima |
|---|---|
| `putin_dushanbe_201baza_preview_720p.mp4` | Koʻrib chiqish uchun 720p nusxa (GitHub’ning 100 MB cheklovi tufayli siqilgan) |
| *(alohida yuborildi)* `putin_dushanbe_201baza_1080p.mp4` | YouTube’ga yuklash uchun master: 1920×1080, 25 fps, H.264 High CRF 18, AAC 320k, −14 LUFS, 6:21.5 |
| `storyboard.md` | 80 ta kadrning timecode, audio matni, fayl, manba va effektlari |
| `manbalar_va_litsenziyalar.md` | Har bir foto/videoning asl URL’i, muallifi, litsenziyasi va videodagi vaqti |
| `youtube_tavsif.txt` | Sarlavha variantlari, boʻlimlar (chapters), creditlar boʻlimi |
| `subtitrlar_uz.srt` | Tuzatilgan oʻzbekcha subtitrlar (YouTube’ga alohida yuklash uchun) |
| `matn_uz.txt` | Ovozning tuzatilgan matni (timecode bilan) |
| `loyiha/` | Tahrirlanadigan loyiha: barcha kadrlar, grafikalar va effektlar kod sifatida |

## Loyihani tahrirlash va qayta render qilish

`loyiha/sb.py` — butun montaj: har bir `shot(boshlanish, tugash, manba, oʻtish)` va har bir grafika
(`LowerThird`, `LocTag`, `FactBox`, `Quote`, `Counter`, `Bars`, `Timeline`, `Compare`, `Kinetic`, xaritalar `MAP(...)`).
Matnni yoki vaqtni oʻzgartirib, qayta render qilish mumkin:

```bash
pip install faster-whisper pycairo pyshp scipy pillow numpy   # ffmpeg ham kerak
export VROOT=/ishchi/papka      # assets/, clips/, web/, audio/ shu yerda
python3 music.py $VROOT/audio/music.wav 381.5      # original fon musiqasi
python3 sfx.py . $VROOT/audio/sfx.wav               # effektlar
for k in 0 1 2 3; do python3 run.py . $k 4 part$k.mp4 & done; wait
```

Ish papkasi tuzilishi: `assets/kremlin/` (kremlin.ru fotolari, `manbalar…md` dagi URL’lar), `assets/commons/`,
`assets/gov/`, `assets/geo/` (Natural Earth 10m), `clips/` (Kremlin HD videolaridan kesilgan parchalar — `kremlin_cliplist.txt`:
nom, video ID, boshlanish soniyasi, davomiyligi), `web/commons_*.json` (Commons metamaʼlumotlari).

Audio zanjiri: ovoz → highpass 75 Hz, yengil shovqin pasaytirish, EQ (−2 dB 250 Hz, +2 dB 3.5 kHz), de-esser, kompressor 2.5:1,
limiter; musiqa ovozga sidechain orqali pasayadi; yakuniy loudnorm −14 LUFS / −1.5 dBTP.
