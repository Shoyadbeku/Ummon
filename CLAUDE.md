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
# (Ko'zga super yelim misoli: zack_test/tools/get_yelim.sh, sahna zack_test/yelim/yelim.py — makro ko'z eye.py, ko'z kesimi (cutaway), timelapse)
# (Ko'z qovog'i uchishi misoli: zack_test/tools/get_qovoq.sh, sahna zack_test/qovoq/qovoq.py — qovoq shape key twitch.py, rentgen nerv + halqa mushak)
# (Uyqu falaji misoli: zack_test/tools/get_falaj.sh, sahna zack_test/falaj/falaj.py — rentgen tana + asab tolalari + qora sharpa)
# (Magnit yutish misoli: zack_test/tools/get_magnit.sh, sahna zack_test/magnit/magnit.py, subtitr zack_test/magnit/subtitr.py)
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

- `Sitting_Drinking` ("having a seat") da qahramon o'tirishdan oldin 180° buriladi: o'tirgan qismida root'ni 180° bur.
  O'ng qo'l og'izga asl ~260–340-kadrda yetadi.
- `Laying_Moaning` da Hips 1.08 m (karavot balandligi), `Laying_3` da 0.07 m; ikkalasida bosh +Y tomonda.
- Harakatlanuvchi bo'sh ob'ektga (zambil) `_par` (matrix_parent_inverse) bilan bola qo'shishdan **oldin** location keyframe qo'yma:
  bo'sh ob'ektni (0,0,0) da yasab, qismlarni qo'shib, keyin harakatni kalitla.
- Rentgen organlar ichidagi magnit ko'rinishi uchun organ materialini 50% Transparent bilan aralashtir, magnitga emissiya ber.
- Subtitr (so'ralsa): Whisper tokenlari ba'zan ikki so'zni birlashtiradi ("ikkhil", "shuyirda") yoki bitta so'zni bo'ladi
  ("kiçki inna", "nersi lar"): `magnit/subtitr.py` dagi FIX ro'yxatini tokenlarga 1:1 mosla ("+" = oldingiga qo'shish, "_" = bo'shliq).
  Shrift: Inter ExtraBold (`fontsdir=/usr/share/fonts/opentype/inter`).
- 40% (432x768), 8 sample: mehmonxona ~9 s/kadr.
- `use_persistent_data = True` bilan uzun renderda rentgen nusxalar (`slot.link="OBJECT"`) dan keyingi kadrlarda Megan tanasi
  qop-qora chiqdi (kasalxona kadri), alohida render qilinganda to'g'ri. Montajdan oldin har kadrdan namuna ol; buzilgan oraliqni
  o'chirib `RANGE=a,b` bilan yangi jarayonda qayta render qil.
- Mixamo'da aksirish harakati yo'q: `aksirish.py: sneeze()` — Spine1/Spine2/Neck/Head ga qo'shimcha burilish kalitlari, alohida harakatga
  yozib NLA track'ga `blend_type="COMBINE"` bilan qo'yiladi. Aktiv harakatni COMBINE qilma: constraint `influence` kalitlari ham o'sha
  harakatga tushadi va qo'shilib ketadi.
- Brian (Mixamo) Head fazosida (X chap, Y tepa, Z old; boshlanishi ~1.57 m): burun uchi (0, 0.052, 0.15), tepa y=0.19.
  Yuz nuqtalarini taxmin qilma, mesh'dan o'lcha (`aksirish.py: HY/HZ`).
- Qo'lni yuzga olib borish: IK nishoni bo'sh ob'ekt, uning bir nechta `COPY_LOCATION` (yuz/tomoq/tirsak) ta'siri kalitlanadi; qo'l
  ko'tarilishidan oldin nishon allaqachon joyida bo'lsin, aks holda bilak (0,0,0) dan uchib keladi (`aksirish.py: drive`).
- Tirsakka aksirish: o'ng bilak boshning chap-old tomonida (Head (0.16, 0.03, 0.12)), alohida IK + pole (Head (-0.25,-0.25,0.5)), `pole_angle=90°`.
- `P.pulse_material` impulsdan keyin butun quvur bo'ylab "iz" (trail) qoldiradi: o'chirish uchun `glow` ni -1.5 ga kalitla va
  materialni emissiyaga qarab Transparent bilan aralashtir (`aksirish.py: pulse_tube`).
- `Laying_Idle` strip'ini `repeat` bilan kadrdan oshirib yuborma: keyingi kadrda qahramon tik turish o'rnida yotib qoladi.
- Ko'chada trotuar 0.14 m baland: qahramon root z ni ham 0.14 qil.
- 40% (432x768), 8 sample: mehmonxona/ko'cha/rentgen ~10 s/kadr (1340 kadr ≈ 3.7 soat).
- `_par` (matrix_parent_inverse) bilan bog'langan qismlar dunyo koordinatasida qoladi: bo'sh ob'ekt (BED) ga mahalliy (0,0,z) berilsa,
  ular (0,0,0) ga — boshqa xonaga — tushadi. Bo'sh ob'ektni (0,0,0) da yasab, joylashuvni `BED + (x,y,z)` qilib ber (`aksirish.py: bl`).
- `Laying_Idle` da Hips root'dan ~1.07 m baland: karavotga yotqizish uchun root z = matras usti − 0.95.
- Batut misoli: `zack_test/tools/get_trampolin.sh`, sahna `zack_test/trampolin/trampolin.py` (choyshab egilishi shape key "dip" = metr,
  prujinalar kadrma-kadr `aim_spring`, sakrash fizikasi `hop_track`, tovush uchun tegish kadrlari `EVENTS=...json`).
- Remy (Mixamo) 2.1x katta yozilgan: root `scale=0.47`; mocap Hips siljishi esa yarmiga qisqaradi (o'tirishda root'ni ~0.2 m qo'shimcha tushir).
- `primitive_cube_add(location=...)` + `transform_apply(scale=True)` dan keyin mesh mahalliy z si joylashuvga siljigan chiqdi: "origin pastda"
  qilish uchun `v.co.z -= min(z)` ishlat, `+= h/2` emas.
- Devor ichiga yashiringan o'sadigan bo'lak (devorni "ko'tarish") devor bilan bir xil qalinlikda bo'lsa, yuzlar ustma-ust tushib devor qop-qora chiqadi:
  bo'lakni 1–2 sm yupqaroq qil. Ob'ektni `scale` bilan o'stirma (BOX tekstura cho'ziladi / qora) — joylashuvini kalitla.
- Basseyn: katta yer tekisligi suv sathidan baland bo'lsa suvni yopib qo'yadi — Boolean bilan teshik och. Kaustika o'chiq bo'lgani uchun
  suv osti qop-qora: suv materialida `Is Shadow Ray` -> Transparent BSDF aralashmasi.
- To'r (batut, futbol darvozasi): Wireframe modifikatori qop-qora devor bo'lib chiqdi; silindr koordinatasidan (atan2, z) PINGPONG chiziqlar bilan Alpha ber.
- 40% (432x768), 8 sample: hovli (HDRI, shaffof suv) ~7 s/kadr (1332 kadr ≈ 2.6 soat).
- Uyqusizlik misoli: `zack_test/tools/get_uyqusizlik.sh`, sahna `zack_test/uyqusizlik/uyqusizlik.py` (yotoqxona + rentgen bosh +
  mikro dunyo: neyronlar, mikroglia, astrotsit, sinapslar; miya "yeyilishi" materiali `brain_mat` — "eat" qiymati).
- Whisper o'zbekchani kirill/qozoq yozuvida chiqarishi mumkin: `initial_prompt` ga lotin yozuvidagi birinchi gapni ber; noaniq
  bo'laklarni `-ss/-to` bilan alohida qayta o'gir.
- `box()` (8 burchakli kub) cho'qqilarini egish butun ob'ektni siljitadi: avval `bmesh.ops.subdivide_edges(cuts=10, use_grid_fill=True)`.
- `Laying_Sleeping`: root z = matras usti − 0.95 (bosh yostiqda). Megan'ning shimi ko'rpadan chiqsa, karavot kadrlarida shim/krossovkani yashir.
- `P.pulse_material` ni takrorlanuvchi impuls bilan ishlatganda "iz" (trail ×4) doimiy yorug'lik beradi va tola oqarib ketadi: o'sha MULTIPLY ni 0 qil.
- `Typing`: Hips 0.56, qo'llar root'dan y −0.5, z 0.78 (stol usti ~0.72). `WoodenTable_01` 0.55 m: z bo'yicha 1.3x.
- 40% (432x768), 8 sample: yotoqxona/mikro dunyo ~9 s/kadr (1044 kadr ≈ 2.6 soat).
- Ovoz fayli yana mos kelmadi (so'rov "mashina" haqida, ElevenLabs mp3 esa uyqu falaji haqida): sahnani **ovoz matniga** qarab qur.
- Blender 5'da POINT chiroqlar kameraga oq shar bo'lib ko'rinadi (qora fonda ayniqsa): `l.visible_camera = False` (`falaj.py: point`).
- AgX Punchy'da to'yingan qizil emissiya (kuch ≳ 3) oq bo'lib chiqadi: qizil ko'z/nuqta uchun 1–2.5 yetarli.
- `Laying_Sleeping`: qahramon yonboshlab yotadi, yuzi +X tomonda (Head Z = +X), qo'llar Hips'dan ~0.19 m baland; `Laying_Breathless` da bosh ~0.25 m ko'tariladi
  (shu kadrlar uchun yuz nuqtasini alohida o'lcha: `falaj.py: FACE2`).
- Parasite (Mixamo) ~2 m, `LeftEye`/`RightEye` va `JawDowm` suyaklari bor (jag'ni mahalliy X bo'yicha ochish). Qop-qora sharpa: base 0.002,
  roughness 1.0, Specular IOR Level 0.05 + Fresnel binafsha chet emissiyasi; aks holda kulrang ko'rinadi.
- Mavjudotni ko'krakka o'tqazish: `Crouching_Idle`, root 180°, `scale=0.92`, z = matras − 0.22. Yondan kamera mavjudot tanasiga to'sib qoladi:
  tepa-yondan (+X +Y, ~1 m) yoki bosh tomondan (karavot suyanchig'i oldidan) yuzga qarat.
- 40% (432x768), 8 sample: yotoqxona/rentgen/tush ~11 s/kadr (1176 kadr ≈ 3.6 soat).
- Megan'da ko'z suyagi yo'q, ko'z va qovoqlar `Body` mesh'ida: qovoq uchishi uchun dam holatida (root (0,0,0)) shape key yasa
  (`qovoq/twitch.py`): chap ko'z markazi dunyoda (0.033, -0.133, 1.624), Head fazosida (0.033, 0.088, 0.135); ko'z soqqasi alohida
  orol — faqat eng katta orol vertekslarini sur. Body va Eyelashes ga bir xil maydon, qiymat 1 ≈ 1.6 mm (makroda yaxshi ko'rinadi).
- Ghost (rentgen) nusxalar `o.copy()` mesh'ni ulashadi: shape key animatsiyasi rentgenda ham ko'rinadi.
- O'tirgan qahramonga tik turgan harakatni (Crying, Drinking, Yawn) berish: action nusxasidan Hips va oyoq kanallarini o'chir
  (`qovoq.py: upper`), NLA da pastdagi Typing oyoqlarni ushlab turadi.
- Nerv bo'ylab "soniyasiga o'nlab" impuls: `fract(u*count - phase)` poyezd materiali, `phase` ni chiziqli kalitla (`qovoq.py: train_mat`).
- 40% (432x768), 8 sample: mehmonxona/rentgen bosh ~10 s/kadr (1186 kadr ≈ 3.3 soat).
- Ovoz fayli yana so'rovdagi misolga mos kelmadi (so'rov: ona/mashina misollari, mp3: ko'zga super yelim): Whisper bilan tekshirib, sahnani ovoz matniga qur.
- `vis(ota, ...)` (recursive) bolalarning `hide_render` kalitlarini o'chirib qayta yozadi: bolaga alohida `vis` ni otadan **keyin** chaqir
  (yelim.py: barmoqlar `eroot` ichida hamma makro kadrda ko'rinib qolgan edi).
- Megan'ning yopiq (yopishgan) ko'zi: ko'z soqqasi orolini (`twitch._islands`, EYE_W ga eng yaqin kichik orol) nusxalab,
  (0.0324, -0.1185, 1.6211) atrofida 1.14x kattalashtirib teri materiali ber; ustiga Head fazosida kiprik/yelim chizig'i (`yelim.py: lidcap, lline`).
- Shisha/naycha yorlig'i: naycha uchi tepada turganda matn to'g'ri o'qilishi uchun matn burilishi (90°, 180°, 0) (mahalliy -Y yuz).
- Makro kadrda kadr kengligi = masofa × 13.5 mm / lens (vertikal sensor 24 mm, 9:16): 10 sm, 42 mm da atigi 3 sm —
  barmoq (1.6 sm) "oq tosh" bo'lib ko'rinadi. Narsalarni kadr kengligiga qarab joylashtir.
- `bpy==5.2.3` o'rnatish yana osilib qoldi: `--timeout 30` bilan qayta ishga tushirish yordam berdi.
- 40% (432x768), 8 sample: mehmonxona/makro ko'z/kesim (yuzlab hujayra sferalari) ~5 s/kadr.

- Ko'zni ishqalash misoli: `zack_test/tools/get_ishqalash.sh`, sahna `zack_test/ishqalash/ishqalash.py` (xona + rentgen bosh: BlenderKit
  ayol bosh suyagi `49c13194`, ko'z olmalari, ko'rish nervlari, miya; makro ko'z; 10x kesim: shox parda yupqalashishi = Solidify `thickness`,
  keratokonus = "cone" shape key, yoriq = Voronoi `DISTANCE_TO_EDGE`; POV fosfenlar shader'i; operatsiya xonasi).
- Ovoz fayli nomi yana mos kelmadi ("koinotdagi ovoz, quyosh..." -> ko'zni ishqalash): Whisper bilan tekshir, sahnani matnga qur.
- `o.copy()` (rentgen nusxa) asl ob'ektning **harakatini ulashadi**: `vis(nusxa, XR)` asl tananing `hide_render` kalitlarini ham qayta yozadi
  (xonada Megan yo'qolib, faqat kipriklari qoldi). Nusxadan keyin `g.animation_data_clear()` qil, keyin ikkalasiga alohida `vis`.
- Bu bpy'da `primitive_plane_add(location=L, rotation=R)` + `transform_apply(scale=True)` joylashuvni ham mesh'ga yozadi (ob'ekt (0,0,0) da qoladi),
  keyin burilish mesh'ni dunyo boshi atrofida aylantirib uzoqqa olib ketadi: plane'ni (0,0,0) da yasab, apply'dan keyin `location`/`rotation` ber.
- BlenderKit bosh suyagi `49c13194` (Draco, 386k vertex): mahalliy -Y old, +Z tepa; Megan `Head` fazosiga `rotation=(-90°,0,0)`,
  `scale=0.8`, joylashuv (0, -0.012, 0.034) — ko'z kosalari Megan ko'zlariga tushadi. Paketdagi `Text.*` ob'ektni o'chir.
- `Crying`: qo'llar ko'zda ~31–75-kadr (30 fps); uzoq ishqalash uchun shu bo'lakni `use_reverse` bilan oldinga/orqaga zanjir qil (sakrash yo'q).
- `Laying_Idle` (inplace=False): Hips 1.08, bosh +Y da 0.55; operatsiya stoli 0.88 da root z = -0.1.
- Shaffof (transmission ≥ 0.7) yupqa shox parda qora fonda ko'rinmay qoladi: 0.4 + emissiya.
- 40% (432x768), 8 sample: xona/rentgen/kesim ~10 s/kadr (1056 kadr ≈ 3 soat).

- Yuzdagi kanalar (Demodex) misoli: `zack_test/tools/get_kana.sh`, sahna `zack_test/kana/kana.py`, modellar `zack_test/kana/mite.py`
  (8 oyoqli kana — oyoqlar `root["ph"]` drayveri bilan yuradi, mikro teri yuzasi teshiklar/tuklar bilan `Skin.H(x,y)`, teri+tuk illizi kesimi).
- Ovoz fayli nomi yana mos kelmadi ("koinotdagi ovoz, quyosh... studio_6" -> yuzdagi Demodex kanalari): har doim Whisper bilan tekshir.
- Whisper o'rta qismni buzib chiqarsa (rus/turk so'zlari), audioni 10 s lik bo'laklarga bo'lib, `initial_prompt` (lotin yozuvidagi birinchi gap)
  va `condition_on_previous_text=False` bilan qayta o'gir; jimlik oralig'ini RMS bilan top.
- `sc.ray_cast` bilan mebel balandligini o'lchashda nurni shiftdan **past**dan boshla (xona shifti 2.7 m — 3.0 dan otilgan nur shiftga tegadi).
- Devordagi rasm ramkasi (`fancy_picture_frame_01`) oynasi Megan'ni aks ettiradi: orqa fonda "ikkinchi Megan" ko'rinsa — ramkani olib tashla.
- Kesimda metaball'ni `bisect` qilib yopish xunuk "silindr" chiqaradi: oddiy sharlar (kesim tekisligida yarmi chiqib turadi) yaxshiroq.
- Mikro dunyo (1000x) chetida ufq qora chiqadi: fon rangini teri rangiga yaqin (0.16, 0.07, 0.055) qil yoki kamerani pastga qarat.
- Xona tashqarisidagi shahar binolari (y −12..−18) uzoqdagi boshqa "dunyo"ning (y −60) fonida ko'rinadi: dunyolarni x bo'yicha ham sur.
- Python `str.__hash__` har jarayonda boshqacha: animatsiyada `hash(name)` ishlatma (qayta ishga tushirilgan render boshqacha harakat beradi).
- Rentgen kanadagi matn (`text_obj`) `(90, 0, 0)` burilish bilan -Y dagi kameraga qaraydi; aks holda teskari ko'rinadi.
- 40% (432x768), 8 sample: mikro teri/kesim/xona ~10–12 s/kadr (960 kadr ≈ 3 soat).
- Ovoz fayli nomi uchinchi marta mos kelmadi ("Koinotdagi ovoz: quyosh..." -> aql tishlari): Whisper bilan tekshirish shart.
- Displace bilan ichkariga siqilgan mesh nusxasi (masalan dentin qatlami) o'zini kesib o'tadi va EXACT boolean jimgina ishlamay qoladi:
  displace'dan keyin voxel remesh qil (`aql/teeth.py: tooth_shapes`).
- Qatlamli kesim (emal/dentin/pulpa, suyak/milk): har qatlamni o'z kesuvchi qutisi bilan 0.5–1 mm oldinroq kes
  (`aql/teeth.py: cutter`), shunda kesim yuzalari bir tekislikda to'qnashmaydi (z-fighting yo'q).
- Kesimni boshqa kadrlarda o'chirish uchun boolean modifierning `show_render` ini keyframe qil (`teeth.key_show`).
- Skan qilingan bosh suyagi (BlenderKit 49c13194) ko'p qatlamli: shaffof rentgen materiali transparent bounce chegarasiga urilib
  qoraygan dog'lar beradi. Shaffofliksiz "fresnel emission" ishlat (`aql.py: xray_solid`).
- Muhitda EGL yo'q: EEVEE render ishlamaydi, prevyu uchun ham Cycles (6–8 sample) ishlat.
- `Sitting_Laughing` boshni orqaga keskin tashlaydi va strip tugagach ham davom etadi: `src=` bilan kesib, `hold=False` qil.
- Ovqatni og'izga olib borish: IK + DAMPED_TRACK (barmoqlar yon-oldinga) + LOCKED_TRACK (kaft tepaga) + barmoq bukish;
  ovqat qo'l suyagidan `fing*0.065 + palm*0.04` da, X o'qi og'izga qaratilgan (`aql.py`).

- Oq sochni yulish misoli: `zack_test/tools/get_oqsoch.sh`, sahna `zack_test/oqsoch/oqsoch.py` (hammom + Kate oq sochni yulishi — IK + Head ga
  `CHILD_OF` rig; bosh terisi makro GN sochlar "Bald" kirishi bilan kal dog'; follikula kesimi: qon tomchilari, chandiq, bakteriya, yiring).
- Ovoz fayli nomi yana mos kelmadi ("koinotdagi ovoz, quyosh... studio_13" -> oq sochni yulish): Whisper bilan tekshir.
- Ota-onaga `vis()` qilingach bolalarda ham `hide_render` kalitlari qoladi: bolani alohida ko'rsatish uchun avval uning fcurve'larini o'chir
  (`oqsoch.py: vis_only`).
- EXACT boolean kesuvchi o'zini kesib o'tsa (ustma-ust qutilar), qatlam jimgina yo'qoladi: `use_self=True`, `use_hole_tolerant=True`.
- Yallig'lanish "nuri" uchun Mix shader (kuch 0 da qora markaz) emas, Transparent + Emission **Add** shader ishlat (`oqsoch.py: glow_mat`).
- 40% (432x768), 8 sample: hammom ~6.5, makro soch ~4.5, kesim (qon/bakteriya/shaffof) 23–35 s/kadr (1063 kadr ≈ 6.3 soat).
