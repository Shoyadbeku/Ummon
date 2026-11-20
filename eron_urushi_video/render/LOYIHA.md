# Tahrirlanadigan loyiha

Video to‘liq kod orqali yig‘iladi — har bir sahna `timeline.py` da (vaqt, kadr, Ken Burns harakati, yozuvlar, o‘tish).

## O‘rnatish
```
pip install numpy pillow pyshp scipy
# ffmpeg va Inter shrifti kerak
```
Papka tuzilishi (loyiha ildizida): `assets/` (materiallar), `ne/` (Natural Earth: ne_50m_admin_0_countries), `audio/`, `render/`.

1. Materiallarni yuklash: `tools/wmcat.py` bilan Commons toifalarini katalogga olish, `tools/fetch2.py` (ro‘yxat — `assets_tanlov.json`).
2. Musiqa/SFX: `python3 render/audio.py 347.9`
3. Tezkor ko‘rish: `python3 render/main.py 960 out/preview.mp4 0 347.9 ultrafast`
4. 4K: `python3 render/main.py 3840 out/video.mp4 0 347.9 faster`
5. Ovoz aralashmasi va muks — README’dagi ffmpeg buyrug‘i.

Matnni o‘zgartirish: `timeline.py` ichidagi `kinetic(...)`, `lower_third(...)`, `quote_card(...)` qatorlari.
Kanal belgisi: `overlays.py` → `bug()`.
