# Editable_Project — 12 yillik ta’lim (news documentary)

Videoni to‘liq qayta yaratadigan loyiha. Montaj kod orqali qilingan: har bir sahna, grafika va sinxron nuqta `render.py` dagi `build()` funksiyasida yozilgan.

## Tarkibi
| Fayl | Vazifasi |
|---|---|
| `prod/render.py` | Kadrlarni chizadi (PIL) va ffmpeg’ga uzatadi. Sahnalar ro‘yxati: `build()`. Manba yozuvlari: `CREDITS` |
| `prod/music.py` | Original fon musiqasi va SFX (whoosh, impact, tick) sintezi |
| `prod/mix.sh` | Ovozga ishlov berish + musiqa (sidechain ducking) + SFX → −14 LUFS |
| `prod/make_docs.py` | `Storyboard.csv` va `Authentic_Media_Sources.csv` ni timeline’dan yig‘adi |
| `tr_large.json` | Whisper large-v3 transkripsiyasi (so‘z darajasidagi vaqtlar bilan) |
| `corrected.txt` | Imlosi tuzatilgan matn (har qator = bitta segment) |
| `imglist.txt` | Rasm kalitlari → Wikimedia Commons fayl nomlari |
| `img/` | Ishlatilgan 15 ta CC rasm (1920–3840 px) |
| `geo/` | Xarita konturlari (world.geo.json) |

## Qayta render qilish
```bash
# kerak: python3, numpy, pillow, ffmpeg, Inter shrifti (/usr/share/fonts/opentype/inter)
cd prod   # render.py yuqori papkadagi tr_large.json, corrected.txt, imglist.txt, img/, geo/ ni o‘qiydi
python3 music.py . 337
./mix.sh /path/to/original_voice.wav mix.wav
N=8404; for i in 0 1 2 3; do python3 render.py part$i.mp4 $((i*2101)) $(( (i+1)*2101 )) & done; wait
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart out.mp4
# bitta kadrni tekshirish:  python3 render.py test.png 3000   (3000-kadr = 120.0 s)
```

## Tipik o‘zgartirishlar
- **Litsenziyalangan YouTube parchasini qo‘shish:** `img/` ga emas, alohida klip sifatida. `build()` da kerakli vaqtga `Shot` qo‘shing (masalan, `P()` o‘rniga videodan kadr o‘qiydigan funksiya) va `CREDITS` ga `VIDEO: Kanal / YouTube` yozuvini kiriting. Tavsiya etilgan vaqt kodlari — `YouTube_Footage_Report.csv` da.
- **Rasmni almashtirish:** faylni `img/<kalit>.jpg` ga qo‘ying va `CREDITS[<kalit>]` ni yangilang.
- **Matn yoki raqamni tuzatish:** `build()` ichida qidiring (masalan, `"BEPUL"`).
- **Brend:** pastki tasma `TICKER` va `draw_chrome()` da.

## Texnik parametrlar
1920×1080, 25 fps, H.264 (yuv420p), AAC 48 kHz stereo, −14 LUFS / −1.5 dBTP.
