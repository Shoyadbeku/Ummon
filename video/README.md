# 3D piyodalar o'tish joyi: Zack D. Films uslubidagi Shorts

| Fayl | Vazifasi |
|---|---|
| `build_scene.py` | Blender sahnasini 0 dan quradi: yo'l, bloklar, anamorfik proyeksiya, odamlar, mashinalar, kameralar, barcha animatsiya. Natija: `scene.blend` |
| `proj.png` | Haydovchi ko'zidan render qilingan "suzuvchi bloklar". U yerga UV Project orqali bo'yoq sifatida tushiriladi. |
| `render_frames.py` | `scene.blend` dagi 885 kadrni `frames/` papkasiga render qiladi |
| `make_audio.py` | Ovoz effektlari (valik, whoosh, mashinalar, tormoz va boshqalar) va fon musiqasini sintez qiladi |
| `audio/s1..s4.wav` | O'zbekcha diktor ovozi (`espeak-ng -v uz`) |
| `assemble.sh` | Kadrlar, ovoz va subtitrlarni yig'ib `final.mp4` yasaydi |

## Qayta yaratish

```bash
pip install bpy numpy          # Blender 5.2 python moduli
python3 build_scene.py         # sahna + proj.png
python3 render_frames.py       # kadrlar (CPU'da ~1.5 soat)
python3 make_audio.py
./assemble.sh                  # final.mp4
```

## Sifatni oshirish

- `build_scene.py` oxirida `resolution_percentage = 100` va `cycles.samples = 64` qo'ying, `use_motion_blur = True` qiling.
- Diktor ovozini o'zingizning ovozingiz yoki ElevenLabs bilan almashtiring. Buning uchun `audio/s1..s4.wav` fayllarini almashtirish kifoya.
- Proksi odam va mashinalarni BlenderKit yoki Mixamo modellari bilan almashtirish mumkin. Ularni `HeroCar`, `Pedestrian`, `Worker` empty'lariga parent qiling.
