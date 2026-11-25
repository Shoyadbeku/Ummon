# Qorong'ida o'qish ko'zga nima qiladi — Zack D. Films uslubida (41.8 s, 9:16, 24 fps, 1004 kadr)

Ovoz: foydalanuvchi yuklagan wav. Fayl nomi "Koinotdagi ovoz: Quyosh aslida qancha jarang" bo'lsa ham,
Whisper matni **qorong'i xonada stol lampasi yoki telefon yorug'ida uzoq o'qish ko'zni zo'riqtirishi** haqida.
Kadrlar so'z vaqtlariga bog'langan.

Zack D. montaji: 23 ta kesish (har 1–2.8 s), hech bir kadr bir joyda turmaydi (doim dolly / orbit / crash zoom),
ilgak (hook): chiroq o'chirgichining makrosi, "chiq" — xona qorong'ilashadi.
Qahramon: Megan (Mixamo, `Writing` o'tirib o'qiydi; `Crying`, `Yawn` faqat tananing yuqori qismiga qatlam qilinadi).
Xona: Poly Haven (metal_office_desk, dining_chair_02, desk_lamp_arm_01, book_encyclopedia_set_01, wooden_bookshelf_worn,
wall_clock, potted_plant_01, fancy_picture_frame_01, laminate_floor_02, painted_plaster_wall, kloofendal HDRI).
Cycles, AgX Punchy, motion blur, DOF.

| # | Kadrlar | Ovoz | Kadr / kamera | Harakat |
|---|---------|------|---------------|---------|
| 1 | 1–24 | "Xonada asosiy chiroq" | **ILGAK. Makro**: devordagi o'chirgich, barmoq bosadi — "chiq", nur so'nadi | — |
| 2 | 25–55 | "o'chirilgan holda," | **Keng, past burchak 16 mm**: shift chirog'i o'chadi, xonada faqat stol ustidagi yorug'lik doirasi qoladi, tez itarish | `Writing` |
| 3 | 56–101 | "faqat bitta kichik stol lampasi," | Past burchak, lampa boshi yonib turadi, nur konusida chang zarralari, orbit | `Writing` |
| 4 | 102–135 | "yoki telefon yorug'ida" | Lampa o'chiq, telefon ekrani yuzni ko'k yoritadi; yuzga yaqin 50 mm f/2 | `Writing` |
| 5 | 136–171 | "uzoq vaqt o'qish" | Devor soati: millar tez aylanadi (vaqt o'tishi), yaqinlashish | — |
| 6 | 172–238 | "ko'z mushaklarini ortiqcha zo'riqtirib qo'yadi." | **Anatomiya studiyasi**: ko'z olmasi va 6 ta mushak, mushaklar qizarib tortiladi, orbit | — |
| 7 | 239–268 | "Atrof qorong'u," | Keng, orqa-yondan: qop-qorong'i xona, kichik yorug'lik oroli, yon tomonga dolly | `Writing` |
| 8 | 269–335 | "o'qiyotgan sahifangiz esa yorqin bo'lganda," | Yelka ortidan yorqin sahifaga, kamera satrlar bo'ylab suriladi | `Writing` |
| 9 | 336–389 | "ko'z har safar qorong'u fonga" | **Makro ko'z** (sovuq nur): qorachiq kattalashadi | — |
| 10 | 390–429 | "va yorug' matnga qaraganda" | Makro ko'z (iliq nur): qorachiq keskin torayadi | — |
| 11 | 430–491 | "qorachig'ini kengaytirib, toraytirib," | Iris ekstremal makro, qorachiq "nafas oladi", crash zoom | — |
| 12 | 492–559 | "fokusni qayta-qayta sozlashga majbur bo'ladi." | **POV sahifa**: fokus qayta-qayta xiralashib-tiniqlashadi | — |
| 13 | 560–598 | "Bu tinimsiz moslashuv" | Ko'z kesimi: gavhar (linza) qalinlashib-ingichkalashadi, nurlar to'r pardada yig'iladi | — |
| 14 | 599–663 | "ko'z ichidagi va atrofidagi mayda mushaklarni" | Kesim + tashqi mushaklar, kiprikli mushak halqasi, orbit | — |
| 15 | 664–693 | "tez toliqtirib," | Mushaklar qizil miltillaydi, crash zoom + silkinish | — |
| 16 | 694–717 | "peshonada, yoki" | Yuzga yaqin: Megan ko'zini ishqalaydi | `Crying` (yuqori tana) |
| 17 | 718–757 | "ko'z ortida og'riq," | **Rentgen bosh**: peshona va ko'z ortida qizil og'riq to'lqinlari | `Crying` (yuqori tana) |
| 18 | 758–795 | "ko'rishning vaqtincha xiralashuvi" | POV sahifa: matn xiralashib, ikkilanadi | — |
| 19 | 796–850 | "va quruqlikni keltirib chiqaradi." | Makro ko'z: qizaradi, qisiladi, pirpiraydi | — |
| 20 | 851–908 | "Garchi bu ko'rishni butunlay buzmasa ham," | O'rta plan yondan: Megan yana o'qiydi, sekin itarish | `Writing` |
| 21 | 909–937 | "charchoq tufayli," | Past burchak: esnaydi | `Yawn` (yuqori tana) |
| 22 | 938–959 | "diqqat pasayadi" | Sahifadagi satrlar suzib, chalkashadi | — |
| 23 | 960–1004 | "va uyqu keladi." | Keng: boshi kitobga tushadi, lampa lip-lip qilib o'chadi → qorong'ilik | `Writing` + bosh egilishi |

Tovush: `sfx.py` (sintez): o'chirgich "chiq", past drone, soat chiqillashi (tezlashadi), kesishlarda "vush",
mushak tortilishida kuchlanish, og'riq pulsi, oxirida lampa o'chishi. Effektlar ovoz ostida avtomatik pasayadi (sidechain).
Subtitr yo'q. Render 540x960 (50%), ffmpeg bilan 1080x1920 ga kattalashtiriladi.
