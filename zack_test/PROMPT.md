# Yangi oynada yoziladigan prompt

Quyidagini nusxalab, `[...]` joylarini o'zgartiring:

```
Zack D. Films uslubida realistik 3D video yasab ber.

VOQEA: [masalan: bir qiz uyida onasi bilan urushib, ko'chaga chiqib, mashinani minib ketib qoldi]
UZUNLIGI: [10] soniya, vertikal 9:16 (1080x1920, sinov uchun 540x960)
OVOZ: [kerak emas / mening klon ovozimda o'zbekcha ovozlashtir: Space Baxtbek97/ummon-ovoz]
SUBTITR: [kerak emas / kerak]

QUYIDAGILARDAN FOYDALAN (hammasi bepul, login kerak emas):
1. Dastur: Blender 5.2, Python moduli sifatida (pip install bpy==5.2.3), Cycles render.
   Sahnani Python kodi bilan yasa, asos sifatida zack_test/scene3.py va zack_test/mixchar.py ni ol.
2. Qahramonlar: Mixamo, Hugging Face'dagi "Linzhan/Mixamo-Animations-Characters" to'plamidan
   (character_refined/*.fbx). Masalan: Megan (qiz), Kate (ona). Boshqa qahramon kerak bo'lsa,
   characters.csv va character_tpose/*.png dan tanla.
3. Harakatlar: o'sha to'plamdagi Mixamo mocap (animation_motion/*.fbx), metadata.csv dan voqeaga mosini top.
   Masalan: Angry_Point, Angry_Gesture_3, Dismissing_Gesture_2, Annoyed_Head_Shake,
   Catwalk_Walk_Start_Turn_180_Right_2, Female_Walk, Entering_Car.
4. Xona va ko'cha: Poly Haven (CC0): mebel (Sofa_01, modern_coffee_table_01, potted_plant_01,
   fancy_picture_frame_01), teksturalar (laminate_floor_02, painted_plaster_wall, asphalt_02,
   concrete_pavement), HDRI osmon (kloofendal_48d_partly_cloudy_puresky).
5. Mashina va boshqa modellar: BlenderKit bepul assetlari (glTF). Masalan, Audi e-tron GT (c3c28d91).
   Draco siqilishini gltf-transform bilan yech. Eshigini kod bilan ajratib, ochiladigan qil.
6. Montaj: ffmpeg (kadrlarni 24 fps MP4 ga yig'ish, ovozni qo'shish).
   Yuklovchi skriptlar zack_test/tools/ papkasida.

KINEMATIKA (Zack D. uslubi): 3–6 ta qisqa kadr; keng plan, yuzga yaqin plan (DOF, orqa fon xira),
past burchakdan keng ob'ektiv, motion blur, AgX Punchy ranglar.

ISH TARTIBI: avval kadr rejasini (storyboard) ko'rsat, keyin 3–5 ta sinov kadrini render qilib
ko'rsat, so'ng to'liq render qil. Tayyor MP4 ni menga yubor va repoga push qil.
CLAUDE.md dagi tuzoqlarni hisobga ol.
```

## Qisqa varianti

```
CLAUDE.md va zack_test/PROMPT.md bo'yicha Zack D. video: [voqea]. [10] soniya, [ovozsiz / mening ovozimda], subtitrsiz.
```

## Ovoz orqali (diktovka) aytish uchun

Uzun matn shart emas, tafsilotlar CLAUDE.md da. Shunchaki ayting:

> "Zak di video qil. [voqea]. O'n soniya."

Ovoz kerak bo'lsa oxiriga "ovozim bilan", subtitr kerak bo'lsa "subtitr bilan" deb qo'shing.
