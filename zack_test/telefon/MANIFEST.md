# Bir ko'z bilan telefon — manifest, render sozlamalari, QA

## Natija
- `bir_koz_telefon.mp4` — 1080×1920 (9:16), 24 fps, 994 kadr, 41.42 s, H.264 High (yuv420p, CRF 20, faststart), AAC 192 kb/s 48 kHz, 35.7 MB.
- Ssenariy/storyboard: `STORYBOARD.md`; sinov kadrlari: `sinov_kadrlar.jpg`.
- Manba kodi: `telefon.py` (sahna), `lib.py`, `sfx.py` (tovushlar), `montaj.sh` (ffmpeg), `../tools/get_telefon.sh` (assetlar), `../yelim/eye.py` (makro ko'z, `PUPIL`).
- `.blend` (89 MB) repoga qo'shilmadi: skript bilan qayta yaratiladi (`SAVE=/path/telefon.blend` env).

## Assetlar va litsenziyalar
| Asset | Manba | Litsenziya |
|---|---|---|
| Megan qahramoni; `Laying_Sleeping`, `Laying_Idle`, `Laying_Shaking_Head`, `Breathing_Idle` | Mixamo (HF dataset `Linzhan/Mixamo-Animations-Characters`) | Mixamo/Adobe shartlari (bepul, loyihalarda foydalanish mumkin; assetni qayta tarqatish mumkin emas — repoda FBX yo'q) |
| HDRI `kloofendal_48d_partly_cloudy_puresky`; teksturalar `laminate_floor_02`, `painted_plaster_wall`; modellar `GothicBed_01`, `ClassicNightstand_01`, `alarm_clock_01`, `potted_plant_01`, `Shelf_01`, `book_encyclopedia_set_01`, `desk_lamp_arm_01` | Poly Haven | CC0 |
| Ayol bosh suyagi `49c13194` | BlenderKit (bepul) | BlenderKit royalty-free |
| Telefon, nur, ko'z kesimi, to'r parda, nervlar, soat | Python kodi (procedural) | loyiha kodi |
| Ovoz (`ovoz.wav`) | Foydalanuvchi yuklagan fayl | foydalanuvchiniki |
| Tovush effektlari | `sfx.py` bilan sintez | loyiha kodi |

Katta binar assetlar (FBX, teksturalar, glb) repoga qo'shilmaydi — `get_telefon.sh` yuklab oladi. Git LFS repoda sozlanmagan;
MP4 (35.7 MB) GitHub 100 MB chegarasidan kichik, avvalgi videolar kabi to'g'ridan-to'g'ri commit qilindi.

## Render sozlamalari
Blender 5.2 (bpy 5.2.3), Cycles CPU (4 yadro), 8 sample + adaptive sampling + denoise, bounces 6 / transparent 24, motion blur
(START), AgX Punchy, 40% (432×768) PNG ketma-ketligi -> ffmpeg lanczos bilan 1080×1920 ga kattalashtirish (foydalanuvchi tanlovi).
Davom ettiriladigan render (`use_overwrite=False`, `use_placeholder=True`). O'rtacha ~11 s/kadr, jami ≈ 3 soat.

## QA
- ffprobe: h264 1080×1920 yuv420p 24/1, 994 kadr; aac 48 kHz; davomiylik 41.417 s; moov boshida (faststart).
- Barcha 994 PNG mavjud, placeholder (< 2 KB) yo'q; o'rtacha yorqinligi < 4 bo'lgan kadrlar faqat 985–994 (rejalashtirilgan qora tugash).
- `blackdetect`: faqat 40.92–41.38 s (yakuniy qorayish). `silencedetect` (−45 dB, 1.5 s): jimlik yo'q.
- Ovoz: mean −14.6 dB, max −0.2 dB (alimiter 0.95).
- Kadrlar har kesishdan namuna bilan ko'zdan kechirildi (persistent-data qora tana muammosi yo'q).
