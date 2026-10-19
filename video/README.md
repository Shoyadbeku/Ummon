# Hikoyali video (CPU, ochiq kod)

Bitta rasm + ovoz + matndan vertikal (720×1280) hikoya videosi yasaydi:
tulki ovozga qarab gapiradi, kadrlar montaj qilinadi, so'zlar ekranda birma-bir chiqadi.

## Kerakli narsalar
- `ffmpeg`, Python 3
- `pip install numpy opencv-python-headless pillow`

## Fayllar
| Fayl | Vazifasi |
|---|---|
| `assets/tulki.jpg` | Asosiy rasm |
| `assets/ovoz.mp3` | Hikoya ovozi |
| `matn.txt` | Subtitr matni |
| `align.py` | So'zlarni ovozdagi vaqtga moslaydi → `words.json` |
| `audio.sh` | Ovozni normallashtiradi va past fon "drone" qo'shadi → `out/audio.m4a` |
| `render.py` | Montaj, og'iz harakati, effektlar, subtitr → `out/hikoya.mp4` |

## Ishga tushirish
```sh
python3 align.py assets/ovoz.mp3 matn.txt words.json
./audio.sh
python3 render.py --preview   # 12 soniyalik tezkor namuna
python3 render.py             # to'liq video
```

## Sozlash
- **Kadrlar montaji**: `render.py` dagi `EDIT` ro'yxati — har qatorda boshlanish soniyasi,
  kadr nomi (`SHOTS` dan), zoom va siljish.
- **Og'iz**: boshqa rasm ishlatsangiz `mouth_pts` (og'iz chizig'i nuqtalari) va `MAX_OPEN` ni o'zgartiring.
- **Subtitr**: shrift `FONT`, joylashuvi `CAP_Y`.
