# zack_test — Zack D. Films uslubidagi 3D shortlar (Blender 5.2 bpy + Cycles)

## Tuzilma
- `tools/fetch_mixamo.py` — HF `Linzhan/Mixamo-Animations-Characters` dan qahramon (`character_refined/`) va harakat (`animation_motion/`) yuklaydi.
- `tools/fetch_polyhaven.py` — Poly Haven CC0 model/tekstura/HDRI (login yo'q).
- `tools/fetch_blenderkit.py` — BlenderKit bepul assetlar glTF ko'rinishida. Keyin Draco ni yechish shart:
  `npx -y @gltf-transform/cli copy in.glb out_dec.glb`
- `water/` — "5–6 litr suv" videosi: `storyboard.md`, `common.py` (umumiy yordamchilar), `film.py` (har kadr alohida sahna),
  `render_all.sh` (kadrlarni render), `edit.sh` (ffmpeg montaj + ovoz).
- Assetlar `assets/`, renderlar `renders/` da (gitga kirmaydi).

## Tuzoqlar (pitfalls)
1. **Skript nomini stdlib moduli nomi bilan atamang** (`inspect.py`, `random.py`...). bpy shu modullarni import qiladi va
   `InitGoogleLogging() twice` bilan qulaydi.
2. **Blender 5.x actionlar slotli**: `action.fcurves` yo'q. F-curvelarga `layers → strips → channelbag(slot).fcurves`
   orqali boring (`common.fcurves`). NLA stripga `strip.action_slot = act.slots[0]` bering.
3. **Mixamo FBX armaturasi `scale=0.01` va `rotation.x=90°` bilan keladi** — `rotation_euler` ni butunlay qayta yozmang,
   faqat `.z` ni o'zgartiring, aks holda qahramon yotib qoladi.
4. **Suyakka (BONE) bog'langan obyekt suyakning *dumida* (tail) turadi**, bone-space birligi sm. Head suyagi 19.6 sm:
   bosh markazi ≈ `(0, -10, 0)`. glTF modellarni boshga qo'yishda X bo'yicha −90° buring.
5. **Mixamo Drinking animatsiyasida shisha CHAP qo'lda**, qahramon −Y tomonga qaragan. Mixamo kliplari 30 fps — 24 fps sahnada
   `speed=1.25` bering.
6. **glTF qayta import qilinganda obyekt nomlari o'zgaradi** (`Circle.000` → `Circle.001` boshqa obyekt bilan to'qnashadi).
   Qismlarni asl *material* nomi (`Circle.000_Baked`) bo'yicha aniqlang.
7. Bo'sh PET shishani qalin glass (transmission) bilan qilmang — sutdek oq chiqadi; Transparent + Fresnel Glossy ishlating.
8. Curve obyektlariga `DISPLACE` modifikatori qo'shilmaydi (`modifiers.new` → None).
9. `view_settings.look` enum fon rejimida bo'sh ko'rinadi, lekin `"AgX - Punchy"` qiymati baribir ishlaydi.
10. CPU da Cycles sekin: 540×960 da render qilib ffmpeg lanczos bilan 1080×1920 ga kattalashtiring, 8–16 sample + OIDN.
    Rentgen kadrlarida kiyim meshlarini yashiring (shaffof qatlamlar render vaqtini 2× oshiradi).
11. `pip install bpy` proksi orqali juda sekin (≈100 KB/s). Wheel'ni `curl -r` bilan 24 bo'lakda parallel yuklab, keyin
    lokal fayldan o'rnating (1 daqiqa).
12. faster-whisper `av.open(metadata_errors=...)` xatosi: audioni ffmpeg bilan 16 kHz float32 raw ga o'tkazib, numpy massiv bering.
13. **`use_persistent_data` + tez deformatsiyalanuvchi qahramon (yiqilish) animatsiya renderida tanani butunlay qora qildi**,
    yakka kadr renderida esa hammasi joyida edi. Bunday kadrlar uchun persistent data ni o'chiring (`film.NO_PERSIST`).
    Renderdan keyin kadrlarni qora piksel ulushi bo'yicha tekshiring.
14. Bo'sh (EMPTY) ota obyektga `hide_render=True` berish bolalarini yashirmaydi — `children_recursive` ni ham yashiring.
15. Konteyner qayta ishga tushishi mumkin: uzoq renderni `setsid nohup` bilan yuriting, `render_all.sh` mavjud kadrlarni
    o'tkazib yuboradi (`use_overwrite=False`), shuning uchun shunchaki qayta ishga tushirish kifoya.
