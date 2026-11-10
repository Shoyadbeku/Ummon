# zack_test — Zack D. Films uslubidagi 3D videolar (Blender 5.2 `bpy`, Cycles)

## Tuzilma
- `common.py` — render sozlamalari (Cycles CPU, OIDN, AgX Punchy), materiallar, kamera yo'llari.
- `mixchar.py` — Mixamo qahramon + harakat (NLA strip) yordamchisi.
- `tools/get_mixamo.sh`, `tools/get_polyhaven.py` — bepul assetlarni yuklash (login kerak emas).
- `tonsil/` — "Tonzillolit" videosi: `STORYBOARD.md`, `room.py`, `shots_room.py` (01–05),
  `throat.py`, `shots_throat.py` (06–14), `render_shot.py`, `montage.sh`.

## Ishga tushirish
```bash
pip install bpy==5.2.3
A=/path/assets
zack_test/tools/get_mixamo.sh $A/mixamo Megan -- Stomach_Hit Taking_Item Annoyed_Head_Shake Breathing_Idle
python3 zack_test/tools/get_polyhaven.py $A/ph model:Sofa_01 model:modern_coffee_table_01 \
  model:potted_plant_01 model:fancy_picture_frame_01 tex:laminate_floor_02 tex:painted_plaster_wall \
  hdri:kloofendal_48d_partly_cloudy_puresky
ZACK_ASSETS=$A python3 zack_test/tonsil/render_shot.py --shot 1 --out frames/s01            # to'liq shot
ZACK_ASSETS=$A python3 zack_test/tonsil/render_shot.py --shot 1 --out test --only 24 30     # sinov kadrlari
zack_test/tonsil/montage.sh frames audio.wav out.mp4
```

## Tuzoqlar (topilgan va hal qilingan)
- **Workbench/EEVEE ishlamaydi**: headless `bpy` `libEGL.so.1` so'raydi. Faqat Cycles; tez
  sinov uchun Cycles `samples=4`.
- **Enum ro'yxatlari bo'sh ko'rinadi**: `bl_rna...enum_items` kontekstsiz `[]` qaytaradi.
  Qiymatni to'g'ridan-to'g'ri o'rnating: `view_transform="AgX"`, `look="AgX - Punchy"`
  (`"Punchy"` emas), `denoiser="OPENIMAGEDENOISE"`.
- **Blender 5 action slotlari**: action ni NLA strip orqali ulang va `strip.action_slot = act.slots[0]`
  ni o'rnating, aks holda armatura qimirlamaydi.
- **Animatsiya FBX o'z armaturasini olib keladi**: import qilib action ni oling va
  yangi ob'ektlarni o'chiring (`mixchar.load_action`).
- **Mixamo root motion**: Hips X/Z siljishini kamaytiring (`_flatten_root`), aks holda qahramon
  kadrdan chiqib ketadi. Bir action ni ikki marta "flatten" qilmang (`act["_flat"]`).
- **NLA tartibi**: ro'yxatdagi keyingi strip ustun turadi. Qisqa harakat (yo'tal) uchun
  `extrapolation="NOTHING"` + `blend_in/out`, aks holda `HOLD_FORWARD` keyingi hammasini bosadi.
- **Og'iz nuqtasi**: suyak offseti noaniq, `Body` meshidan lab vertexini oling
  (`shots_room.mouth`). Bosh suyagi: lokal Y = yuqori, lokal Z = oldinga; FBX masshtabi 0.01 (sm).
- **`Object.cast_shadow` Blender 5 da yo'q** (`visible_shadow` ishlating yoki tegmang).
- **CPU render sekin** (4 yadro, GPU yo'q): 576×1024 da render qiling va ffmpeg bilan
  1080×1920 ga kattalashtiring. `samples=10–12` + OIDN, `subsurface_method="BURLEY"`
  (random walk dan ~2 baravar tez), `use_persistent_data=True`. Ikkita render jarayonini
  parallel ishlatish umumiy tezlikni oshiradi (har kadr sahnani yangilash bitta yadroda).
- **Ochiq makro sahnalarda ufq** qora ko'rinadi: atrofni gumbaz (dome) bilan yoping.
- **revolve() normallari**: tunnel/tomir ichidan ko'riladi, `flip=True` (SSS to'g'ri ishlashi uchun).
- **Ovoz fayl nomi aldashi mumkin**: matnni oldin Whisper bilan o'qing (faster-whisper ga
  `av` versiyasi mos kelmasa, ffmpeg bilan 16 kHz float32 PCM ga o'girib, numpy massiv bering).
