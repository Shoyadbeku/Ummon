# Ummon: Claude uchun ko'rsatma

Foydalanuvchi o'zbek tilida yozadi, javob ham o'zbekcha bo'lsin.

## Foydalanuvchi ovoz orqali yozadi (diktovka)

Xabarlar ovozdan matnga o'girilgan bo'ladi: imlo xatolari, tinish belgisiz gaplar va noto'g'ri yozilgan
nomlar bo'lishi tabiiy. "zack d", "zak di", "zakdi", "zack d filmsday", "zek di films" kabilarning
hammasi **Zack D. Films** degani. Qisqa buyruqni to'liq vazifa deb tushun va savol bermasdan boshla.

Masalan: "zak di video qil qiz onasi bilan urushib mashinada ketib qoldi o'n soniya ovozim bilan".

Sukut bo'yicha (foydalanuvchi boshqacha aytmasa):
- uzunlik 10 soniya, vertikal 9:16;
- subtitr yo'q;
- ovoz yo'q. Faqat "ovozim bilan", "mening ovozimda", "ovozlashtir" desa, klon ovoz qo'shiladi;
- `zack_test/PROMPT.md` dagi manbalar va kinematika qo'llaniladi;
- avval 3–5 ta sinov kadrini ko'rsatib, keyin to'liq render qilinadi.

## "Zack D. Films uslubida video" so'ralsa

Foydalanuvchi qisqa voqea aytadi (masalan "qiz onasi bilan urushib, mashinada ketib qoldi") va
uni o'z ovozida ovozlashtirishni so'raydi. Ish tartibi:

1. **Ssenariy.** Voqeani 3–6 ta kadrga bo'l (kadr ro'yxati + kamera burchagi). Ovozli izoh matni
   o'zbekcha, qisqa, Zack D. ohangida bo'lsin ("Agar ... bo'lsa, nima bo'ladi?"). Uzunlik foydalanuvchi
   aytganicha, aytilmasa 10–20 soniya.
2. **Ovoz (foydalanuvchining klon ovozi).** Hugging Face Space `Baxtbek97/ummon-ovoz`, API `/ovozlashtirish`:
   ```bash
   B=https://baxtbek97-ummon-ovoz.hf.space/gradio_api/call/ovozlashtirish
   ID=$(curl -sS -X POST $B -H 'Content-Type: application/json' \
        -d '{"data": ["MATN", "Sardor (erkak)", 0, 0, 0.33]}' | python3 -c "import json,sys;print(json.load(sys.stdin)['event_id'])")
   curl -sS -N $B/$ID   # oxirgi "data:" qatorida audio fayl URL'i bo'ladi -> curl bilan yuklab ol
   ```
   Parametrlar: matn, asosiy ovoz ("Sardor (erkak)" yoki "Madina (ayol)"), tezlik %, ohang (yarim ton), protect.
   Space uxlab yotgan bo'lsa, birinchi so'rov 1–2 daqiqa olishi mumkin. Ishlamasa, foydalanuvchiga ayt,
   o'rniga ovoz yasab qo'yma.
3. **Sahna (Blender, `zack_test/scene3.py` asosida).** Kadrlar sonini ovoz uzunligiga moslab qo'y (24 fps).
4. **Render va montaj.** `ffmpeg` bilan kadrlarni MP4 ga yig'ib, ovozni qo'sh.
   Subtitr faqat so'ralsa qo'shiladi.
5. Natijani `zack_test/` ga qo'y, commit qil, push qil va faylni foydalanuvchiga yubor.

## Muhitni tayyorlash (har yangi sessiyada)

```bash
python3 -m venv /tmp/claude-0/bvenv && /tmp/claude-0/bvenv/bin/pip install -q bpy==5.2.3
zack_test/tools/get_mixamo.sh                      # Megan (qiz), Kate (ona) + harakatlar, HF to'plami
# (Illyuminator misoli: zack_test/tools/get_samolyot.sh + get_illyuminator.sh, sahna zack_test/illyuminator/illyuminator.py)
# (Phineas Gage misoli: zack_test/tools/get_mixamo_gage.sh, sahna zack_test/gage/gage.py, montaj zack_test/gage/montaj.sh)
# (Ebbi/ko'z chuvalchangi misoli: zack_test/tools/get_ebbi.sh, sahna zack_test/ebbi/ebbi.py, makro ko'z/pashsha/barmoq: zack_test/ebbi/eye.py)
python3 -I zack_test/tools/ph_get.py Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 \
  kloofendal_48d_partly_cloudy_puresky laminate_floor_02 asphalt_02 concrete_pavement painted_plaster_wall
zack_test/tools/bk_get.sh "car" c3c28d91 /tmp/claude-0/assets/bk   # Audi (BlenderKit, bepul)
mkdir -p /tmp/claude-0/tools && (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
/tmp/claude-0/tools/node_modules/.bin/gltf-transform copy /tmp/claude-0/assets/bk/c3c28d91.glb /tmp/claude-0/assets/bk/c3c28d91_u.glb
```
Render: `OUT=/tmp/claude-0/frames/ SAMPLES=14 /tmp/claude-0/bvenv/bin/python -I zack_test/scene3.py --render`
(sinov uchun: `FRAMES=30,120,200 PCT=35`). 50% (540x960) da bir kadr taxminan 15–25 soniya.

## Manbalar (login kerak emas)

- **Qahramonlar va harakat:** HF dataset `Linzhan/Mixamo-Animations-Characters` (114 qahramon, 2317 mocap).
  Ro'yxat: `characters.csv`, `metadata.csv`; ko'rish uchun `character_tpose/*.png`, `animation_motion_render/*/v000.mp4`.
- **Muhit:** Poly Haven (CC0): HDRI, teksturalar, mebel.
- **Mashina va boshqa modellar:** BlenderKit bepul assetlari (`is_free:true`, gltf).
- **Ishlamaydi:** Mixamo saytining o'zi va Sketchfab (login kerak), Daz va Character Creator (Windows dasturi).
  MPFB2 kodini ishga tushirishni xavfsizlik tizimi bloklaydi.

## Ma'lum tuzoqlar

- Skriptlarni `python -I` bilan ishga tushir (`inspect.py` kabi nomlar stdlib'ni to'sib qo'yadi).
- Mixamo FBX import qilingach, `arm.animation_data.action = None` qil, aks holda T-poza NLA'ni bosib qo'yadi.
  Blender 5'da NLA strip uchun `strip.action_slot = act.slots[0]` kerak (`mixchar.py` buni qiladi).
- Mixamo 30 fps, sahna 24 fps: strip scale = 0.8 / speed.
- `Entering_Car`: qahramon mashina yo'nalishiga qarab turadi, eshik uning **chap** tomonida bo'ladi.
- BlenderKit glb fayllari Draco bilan siqilgan, bpy g'ildiragi ularni ocha olmaydi: avval `gltf-transform copy` qil.
- Poly Haven API'da modellarda ham `Diffuse` kaliti bor, turini `/info/<id>` dagi `type` bilan aniqla.
- Ovoz fayli nomi mazmunini aks ettirmasligi mumkin: avval Whisper bilan matnga o'gir
  (`faster-whisper`, `medium`, `language="uz"`, `word_timestamps=True`) va kadrlarni so'z vaqtlariga bog'la.
  faster-whisper'ning PyAV'si bilan wav ochilmasa, audioni ffmpeg orqali numpy massiv qilib ber.
- Poly Haven API `User-Agent` sarlavhasisiz 403 qaytaradi (`ph_get.py` buni qo'yadi).
- `rock_moss_set_01` kabi `*_set_*` modellari bitta tosh emas, 10 m+ ga yoyilgan to'plam: kadrni to'sib qo'yadi.
- `primitive_*_add(rotation=...)` bilan yasalgan mesh'ni `join` qilgach `transform_apply` qil, aks holda
  ob'ektning o'z burilishi qoladi va mesh kutilgan o'q bo'ylab yo'nalmaydi.
- Mixamo `mixamorig:Head` suyagi o'qlari (dunyoda, masshtabsiz): X = qahramonning chapi, Y = tepa, Z = old.
  Boshga narsa yopishtirish uchun bo'sh ob'ektga `CHILD_OF` (subtarget Head, `use_scale_*=False`, inverse = identity).
- Baland qoyalar (≥ 10 m) o'yiqda quyoshni to'liq to'sadi: 5–6 m yetarli, quyosh balandligi ≥ 55°.
- 4 yadroli muhitda 540x960, 10 sample: ~15 s/kadr. Uzoq render uchun `nohup setsid ... &` va
  `use_overwrite=False` + `use_placeholder=True` (to'xtasa, qayta ishga tushirsa davom etadi).
- Makro kadrlarda (ko'z, hasharot) kamera `clip_start` ni 0.001 qil: sukut bo'yicha 0.1 m, undan yaqin hamma narsa kesilib ketadi.
- Blender 5'da `shape_key_add(from_mix=False)` yangi kalitning qiymatini 1.0 qiladi: darhol `kb.value = 0` qil.
- Principled `Subsurface Scale` sukut bo'yicha 0.05 m: kichik ob'ektlarda (ko'z, chuvalchang) 0.0005 atrofida qo'y, aks holda tekstura yuvilib ketadi.
- Mixamo qahramonlari root burilishi 0 da -Y tomonga qaraydi (+Y ga qaratish uchun 180°).
- Kesishlarda (kamera markerlari) motion blur qo'shni kadrni aralashtirmasligi uchun `motion_blur_position = "START"`.
- Petri idishidagi suyuqlik (transmission) ichiga botgan ob'ektlar qora chiqadi: suyuqliksiz qil yoki ob'ektni sirtdan chiqar.
- Mixamo `Crying` harakatida qo'llar yuzga ~25-kadrda yetadi: strip'ni kadr boshidan ~25 kadr oldin boshla.
- Blender 5.2'da Geometry Nodes modifier kirishlari `mod["Socket_1"]` emas: `getattr(mod.properties.inputs, "Socket_1").value`,
  keyframe: `x.keyframe_insert("value", frame=f)` (`burish/parts.py: key_mod`).
- Blender 5.2'da `Curve.use_uv_as_generated` yo'q: egri bo'ylab impuls uchun GN (Curve to Mesh + Spline Parameter -> "u" atributi),
  shaderda Attribute "u" (`parts.tube_group`).
- `o.parent = stansiya_empty` (masalan (20,0,0) da) qilinsa, bola dunyo koordinatasida ikki marta siljiydi: `matrix_parent_inverse` qo'y
  (`burish.py: _par`).
- Megan'ning `Body` meshi faqat bosh, qo'l, oyoq: kiyim ostida tana yo'q. Vannada futbolka materialini teri rangiga almashtir, shim/krossovkani yashir.
- Qo'l pozasi: `RightForeArm` ga IK (`use_tail=True`, chain 2), `RightHand` ga DAMPED_TRACK (Y = barmoqlar) + LOCKED_TRACK (TRACK_Z = kaft);
  barmoq bukish: TRANSFORM constraint, mahalliy X +65°.
- Makro (1–10 sm) kadrlarda f/4–11 da fokus juda yupqa: f/22 qo'y, lens ≤ 50 mm.
- Og'ir GN/Solidify modifikatorlarini `show_viewport=False` qil: skriptdagi `frame_set` sikllari 6 daqiqadan bir necha soniyaga tushadi.
- Ovoz fayl nomi yana mos kelmadi ("Neytron yulduzi..." -> barmoqlar burishishi): har doim Whisper bilan tekshir.
- Whisper o'zbekcha ovozni qozoqcha deb aniqlashi mumkin: `language="uz"` ni doim aniq ber.
- `pip install faster-whisper` osilib qolsa (CPU 0%), to'xtatib `--timeout 30` bilan qayta ishga tushir.
- `Drinking` harakatida idish **chap** qo'lda (`LeftHand`). Narsani tik ushlatish uchun: kaftga `CHILD_OF` bo'sh ob'ekt,
  narsaning o'ziga esa faqat `COPY_LOCATION` (`use_offset=True`), burilishini o'zing qo'y (`muzlash.py: coneR`).
- `Agony` da qahramon qattiq egilib, yuzi yerga qaraydi: yaqin plan uchun `Focus` ning birinchi 2.5 s i (tik turib boshini ushlaydi).
- Rentgen bosh ichiga organ qo'yish (tanglay, til, tishlar): qismlarni mahalliy koordinatada yasab, `Head` ga bog'langan
  bo'sh ob'ekt ichiga `scale=0.1`, `rotation=(-90°,0,0)` bilan joylash (sahna o'qlari: -Y old, +Z tepa) — `muzlash.py: build_mouth`.
  Kamerani boshga `COPY_LOCATION` qilingan rig'ga bog'la, shunda u bosh bilan birga yuradi.
- 45% (486x864), 8 sample: ko'cha ~15 s, rentgen bosh ichidagi og'iz ~30 s/kadr (shaffof qatlamlar sekin).
- Hiqichoq (hiccup) uchun Mixamo'da tayyor harakat bor: `Drunk_Idle_Variation` ("Drunk Idle Variation Hiccup"), silkinish
  strip boshidan ~13 kadrdan keyin. Yetarlicha sezilmaydi: `root` ga 1–2 kadrlik qo'shimcha tepaga/orqaga silkinish kalitini qo'sh (`hiqichoq.py: JOLTS`).
- `Drinking` da bankani `LeftHand` ga `CHILD_OF` qilib, banka o'qini qo'lning X o'qiga burish kifoya (`rotation=(0, 90°, 0)`), `speed=0.6` bilan
  og'izda ~45 kadr turadi.
- Shaffof bo'lmagan quvur (traxeya) ichidagi zarralar ko'rinmaydi: quvur materialiga `Alpha` 0.4 qo'y.
- `bpy.data.objects.new` bilan yasalgan ob'ektga `matrix_parent_inverse = parent.matrix_world.inverted()` ni `view_layer.update()` siz
  qo'yma (matritsa hali birlik bo'ladi, ob'ekt ikki marta siljiydi) — oddiy `o.parent = p` va mahalliy koordinata yetarli.
- 45% (486x864), 8 sample: mehmonxona/studiya/rentgen ~12 s/kadr (960 kadr ≈ 3 soat).
- Mixamo FBX importi sahnani **30 fps** ga o'zgartiradi: har `load_character`/`load_action` dan keyin `sc.render.fps = 24` qil,
  aks holda NLA strip masshtabi 1.0 bo'lib qoladi va GN `Scene Time` (yomg'ir/qor) noto'g'ri vaqtni beradi (`qulf.py: A_`).
- Yomg'ir/qor uchun GN zarralarini aylantirma (modulo): aylangan tomchi motion blur'da butun kadr bo'ylab chiziq beradi.
  Har tomchi kadr davomida bir marta tushsin (ustun balandligi = H + tezlik × davomiylik) — `qulf.py: precip`.
- Kesim (cutaway) uchun boolean kesuvchilarni ob'ektni ota-onaga (`parent`) bog'lashdan **oldin** qo'lla: kesuvchilar dunyo
  koordinatasida bo'ladi.
- 45% (486x864), 8 sample: hovli/makro/kesim studiyasi ~7.5 s/kadr (963 kadr ≈ 2 soat).
- BlenderKit illyuminator (7250f009) ichki oq qopqog'ini **material nomi** (`Circle.002_Baked`) bo'yicha o'chir: har importda ob'ekt
  qayta nomlanadi (Circle.008...), `name.startswith("Circle.002")` faqat birinchisini topadi va derazalar oq bo'lib qoladi.
  Paketda 2 m lik `Cube` ham bor: `max(o.dimensions) > 1` ni ham o'chir (`illyuminator.py: is_cover`).
- `Falling_Into_Pool_2`, `Edge_Slip` kabi "chetdan" harakatlarda Hips 0.5–1.3 m baland yozilgan: root z ni pasaytir yoki boshqa harakat tanla.
- Salonda o'rindiq qadami 0.82 m: kamera oldingi qator suyanchig'i (x = qator − 0.5) ortida qolsa, kadrni to'sadi.
  Yaqin plan uchun kamerani x ∈ [qator − 0.45, qator − 0.3] yoki z ≥ 1.4 ga qo'y.
- Deraza yonidagi to'ldiruvchi AREA chiroq kameraga oq to'rtburchak bo'lib ko'rinadi: `visible_camera = False`.
- `P.crack_strip` zigzagi 1.2 sm qat'iy: kichik oyna uchun yoriqni 3x yasab `scale = 1/3` qil.
- Matnni kadrga qarab o'zgartirish (harorat ekrani): `frame_change_pre` handler ichida qiymatni animatsiyadan emas, kadr raqamidan hisobla.
- Bu sahnada 30%, 6 sample: ~10 s/kadr (hajmli tuman bilan ham).

