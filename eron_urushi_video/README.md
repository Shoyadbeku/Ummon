# «Eron urushi: 9-oy» — montaj hisoboti

**Audio:** `Neytron_yulduzining_…_SadoStudio 14.wav` (iCloud) — 5:47,9, 48 kHz mono.
> ⚠️ Fayl nomi «Neytron yulduzi» bo‘lsa-da, ovoz mazmuni **Eron atrofidagi urush** haqida. Video shu mazmun bo‘yicha qilindi.

## Natija fayllari
| Fayl | Tavsif |
|---|---|
| `eron_urushi_9oy_4K.mp4` | 3840×2160, 25 fps, H.264 (High), AAC 320 kbps, −14 LUFS — YouTube’ga yuklash uchun (sessiyada; hajmi katta, GitHub’ga sig‘maydi) |
| `eron_urushi_9oy_1080p.mp4` | 1920×1080 nusxa (repoda) |
| `ovoz_subtitr_uz.srt` | O‘zbekcha subtitr (YouTube’ga alohida yuklanadi) |
| `transkripsiya_uz.txt` | Tuzatilgan to‘liq matn, timecode bilan |
| `youtube_tavsif.txt` | Tavsif (<5000 belgi): bo‘limlar + creditlar |
| `manbalar_toliq_royxat.txt` | Har bir material: nomi, muallifi, litsenziyasi, havolasi (pin izoh uchun) |
| `render/` | Tahrirlanadigan loyiha: Python timeline (`timeline.py`) — kadrlar, vaqtlar, matnlarni o‘zgartirib qayta render qilish mumkin |

## Ish jarayoni
1. **Audio tahlili** — Whisper large-v3 bilan transkripsiya, keyin qo‘lda tuzatildi (142 segment).
2. **Material qidirish** — Wikimedia Commons («Videos of 2026 Iran war», «Operation Epic Fury», «Islamabad Talks», Mehr/Avash fotolari va h.k.), NASA SVS (keraksiz chiqdi), Natural Earth xaritalari. Faqat **Public domain / CC0 / CC BY / CC BY-SA** materiallar ishlatildi.
3. **Storyboard** — 68 sahna (pastdagi jadval).
4. **Montaj** — o‘zim yozgan Python + FFmpeg dvigateli: Ken Burns, lower third’lar, kinetik tipografiya, animatsion xaritalar (raketa traektoriyasi, parvoz yo‘nalishlari, xavfli havo hududi), diagrammalar (Senat ovozi, $48,3 mlrd hisoblagich, Brent narxi), flash/dissolve/push o‘tishlar, rang korreksiyasi va vinyetka.
5. **Ovoz** — shovqin kamaytirish (afftdn), EQ, de-esser, kompressor; original sintez qilingan fon musiqasi ovoz ostida avtomatik pasayadi (sidechain ducking); whoosh/impact effektlari; −14 LUFS.
6. **Manbalar** — har bir tashqi kadrda pastki chapda manba + litsenziya; arxiv kadrlar «ARXIV» deb belgilangan.

## ⚠️ Faktlarni tekshirish kerak bo‘lgan joylar
Men ularni mustaqil manbada to‘liq tasdiqlay olmadim — yuklashdan oldin tekshiring:
- **Senatdagi 51–48 ovoz (19-noyabr).** Topilgan manbalarda faqat 23-iyundagi 50–48 ovoz bor (o‘shanda rezolyutsiya *qabul qilingan*). Noyabr ovozini tasdiqlovchi manba topilmadi.
- **NYT: «4–7 kunlik kampaniya».** Topilgan manbalarda «3 kunlik» va «48 soatlik» rejalar haqida yozilgan; aniq «4–7 kun» topilmadi.
- **Brent narxi.** Audioda «taxminan 92,5 dollar» deb eshitiladi (Whisper ikki marta shunday aniqladi); grafikada 92,5 $ va +28% ko‘rsatilgan.
- **Eron qo‘mondoni ismi.** Audioda noaniq (taxminan «Abdurahim Musaviy»); ekranda faqat «Eron qo‘mondoni» deb berildi.
- **Pentagon rasmiysi Artur Miller** va **$48,3 mlrd** — mustaqil manbada tekshirilmadi.
- Tasdiqlangan: Trampning Barak Ravid (Axios) bilan intervyusi, «yangi yildan keyin ko‘ramiz» iborasi; IEA rahbari Fatih Birolning «tarixdagi eng katta energetika inqirozi» bayonoti.

## Cheklovlar (ochiq aytaman)
- **Reuters, CNN, BBC, X, Telegram va YouTube’dagi yangilik lavhalari ishlatilmadi**: ular mualliflik huquqi bilan himoyalangan va litsenziyasiz montajga qo‘shish strike xavfini tug‘diradi. Ularning o‘rniga AQSh hukumatining public domain kadrlari va Eron agentliklari (Mehr, Avash)ning CC BY 4.0 materiallari olindi.
- **Riyoddagi 19-noyabr zarbasi, husiylar va Hormuzdagi tankerlarning aynan o‘sha kungi kadrlari** ochiq litsenziya bilan topilmadi — o‘rniga arxiv suratlari (PIF minorasi, KAFD) va xaritalar ishlatildi, ekranda «ARXIV» deb yozildi.
- Yandex Images, DVIDS sayti va bir nechta Eron saytlari bu muhitdan bloklangan; Wikimedia’dan yuklashda so‘rov cheklovi tufayli 6 ta qo‘shimcha video (B-2, Mehr’ning ikki klipi va boshqalar) yetib kelmadi.
- Manbalarning aksariyati 1080p — 4K nusxa ularni kattalashtirgan (grafikalar 4K’da chizilgan va tiniq).
- Fair use kafolat emas: bu yerda public domain/CC materiallar ishlatilgani uchun xavf past, lekin Content ID baribir da’vo qilishi mumkin (ayniqsa Oq uy/Pentagon kadrlari boshqa kanallarda ham bor).
- Kanal nomi/logotip qo‘yilmadi (yuqori chapda neytral «TAHLIL» belgisi). Kerak bo‘lsa, `overlays.py` → `bug()` funksiyasida o‘zgartiriladi.

## Storyboard (timecode bo‘yicha)
| # | Vaqt | Ovoz (narrator) | Kadr / grafika | Manba · litsenziya | O‘tish |
|---|---|---|---|---|---|
| 1 | 00:00.00–00:02.30 | 9 oyga yaqin davom etayotgan urush. | Epic Fury Strike compilation (997841).webm | Public domain | cut |
| 2 | 00:02.30–00:05.38 | 48 milliard dollardan ortiq xarajat. | USS Spruance (DDG 111) Fires Tomahawk Land Attack Missiles (997963).we | Public domain | flash |
| 3 | 00:05.38–00:12.85 | Xalqaro energetika agentligi rahbari esa bu inqirozni energetika xavfsizligi tarixidagi eng katta tahdid deb atadi. | Fatih Birol - 2021 (51714983107).jpg | CC BY 2.0 | dissolve |
| 4 | 00:12.85–00:16.55 | Bugun Eron atrofidagi urush yana yangi bosqich arafasida turibdi. | KC-135 Stratotanker refuels Fighter Aircraft during Operation Epic Fur | Public domain | dissolve |
| 5 | 00:16.55–00:19.30 | Savol esa bitta: yangi zarbalar bo‘ladimi? | U S B-1 bombers take off to support Operation Epic Fury (997873).webm | Public domain | flash |
| 6 | 00:19.30–00:23.70 | Assalomu alaykum. Avval asosiy voqealarni eslab o‘tamiz. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | flash |
| 7 | 00:23.70–00:26.90 | Shu yilning fevral oyi oxirida Amerika Qo‘shma Shtatlari va Isroil Eronga qarshi keng ko‘lamli harbiy operatsiya boshladi. | U.S. Forces Launch Operation Epic Fury.webm | Public domain | dissolve |
| 8 | 00:26.90–00:30.00 | Amerika Qo‘shma Shtatlari va Isroil Eronga qarshi keng ko‘lamli harbiy operatsiya boshladi. | U S forces Execute large-scale Precision Strike on Kharg Island, Iran  | Public domain | cut |
| 9 | 00:30.00–00:33.90 | O‘shandan beri vaqtinchalik sulhlar e’lon qilindi, muzokaralar bo‘ldi, | Sidelines of Islamabad Talks 1.jpg | CC BY 4.0 | dissolve |
| 10 | 00:33.90–00:38.15 | biroq urushni to‘liq tugatadigan barqaror kelishuvga hali erishilmagan. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 11 | 00:38.15–00:39.55 | Hujumlar va javob zarbalari to‘xtamayapti. | Attack on areas north of Tehran 1 Avash 20 esfand 1404.webp | CC BY 4.0 | flash |
| 12 | 00:39.55–00:40.90 | Hujumlar va javob zarbalari to‘xtamayapti. | CENTCOM Completes Strikes on IRGC Targets in Iran (1021498).webm | Public domain | cut |
| 13 | 00:40.90–00:44.00 | So‘nggi ikki kunda esa vaziyat yana keskinlashdi. | USS Abraham Lincoln Conducts Night Flight Operations (1000024).webm | Public domain | cut |
| 14 | 00:44.00–00:49.60 | Birinchi muhim xabar Vashingtondan keldi. 19-noyabr kuni prezident Donald Tramp | President Donald J. Trump on the United States Military Major Combat O | Public domain | flash |
| 15 | 00:49.60–00:53.00 | isroillik jurnalist Barak Ravidga bergan intervyusida shunday dedi: | NYCW 2025 - Barak Ravid 01.jpg | CC BY-SA 4.0 | dissolve |
| 16 | 00:53.00–00:59.10 | «Eron bo‘yicha qaror qabul qilishga shoshilmayapman. Yangi yil boshlangandan keyin nima bo‘lishini ko‘ramiz». | President Donald J. Trump on the United States Military Major Combat O | Public domain | dissolve |
| 17 | 00:59.10–01:02.55 | Birinchi qarashda bu taranglikni yumshatadigan gapdek eshitiladi. | President Donald J. Trump oversees Operation Epic Fury at Mar-a-Lago ( | Public domain | dissolve |
| 18 | 01:02.55–01:09.85 | Lekin aynan shu kuni Bloomberg va The New York Times AQShning yangi zarbalarga tayyorgarlik ehtimoli oshib borayotgani haqida yozdi. | USS Abraham Lincoln supports Operation Epic Fury (998342).webm | Public domain | cut |
| 19 | 01:09.85–01:18.50 | The New York Times ma’lumotiga ko‘ra, Isroil bosh vaziri Binyamin Netanyaxu to‘rt kundan yetti kungacha davom etadigan yangi harbiy kampa… | President Donald J. Trump meets with Israeli Prime Minister Benjamin N | Public domain | dissolve |
| 20 | 01:18.50–01:22.00 | Bundan bir kun oldin Tramp Fox News telekanaliga intervyu bergan edi. | President Donald J. Trump and Secretary of War Pete Hegseth speak on O | Public domain | dissolve |
| 21 | 01:22.00–01:27.40 | Unda u Eron kimyoviy yoki biologik qurol ustida ishlayotgan bo‘lishi mumkinligini aytdi. | President Donald J. Trump on the United States Military Major Combat O | Public domain | cut |
| 22 | 01:27.40–01:35.30 | Tehron bu ayblovni keskin rad etdi. Eron Tashqi ishlar vazirligi vakili Ismoil Baqoiy buni xuddi o‘sha yolg‘on ssenariy deb atadi. | Press Conference of Esmail Baghaei 12 (Mehr, 15 April 2026).jpg | CC BY 4.0 | dissolve |
| 23 | 01:35.30–01:38.80 | Ikkinchi muhim voqea Amerika Qo‘shma Shtatlari Kongressida bo‘ldi. | Capitol Building Full View.jpg | Public domain | flash |
| 24 | 01:38.80–01:46.20 | 19-noyabr kuni Senat Eron urushini to‘xtatish yoki uni davom ettirish uchun Kongress ruxsatini talab qiladigan rezolyutsiyani ovozga qo‘ydi. | 111th US Senate class photo.jpg | Public domain | dissolve |
| 25 | 01:46.20–01:51.90 | Natija: 51 ovoz qarshi, 48 ovoz tarafdor. Rezolyutsiya rad etildi. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | push |
| 26 | 01:51.90–01:59.90 | Bu noyabrdagi oraliq saylovlardan keyingi birinchi shunday ovoz berish edi. Natija shuni ko‘rsatdiki, Oq uyning qo‘li hozircha bo‘sh. | North Façade White House.JPG | Public domain | dissolve |
| 27 | 01:59.90–02:06.80 | Uchinchi voqea urush narxi bilan bog‘liq. Pentagon rasmiysi Artur Miller Senatdagi tinglovda raqamni e’lon qildi. | OEF Press Briefing (9549055).jpg | Public domain | flash |
| 28 | 02:06.80–02:13.40 | Uning so‘zlariga ko‘ra, 13-noyabr holatiga ko‘ra urush AQShga 48 milliard 300 million dollarga tushgan. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 29 | 02:13.40–02:19.15 | Miller bu summaga o‘q-dorilar, texnikani almashtirish va operatsion xarajatlar kirganini aytdi. | USS Bainbridge (DDG-96) supports Operation Epic Fury (998182).webm | Public domain | cut |
| 30 | 02:19.15–02:24.00 | Harbiy bazalarga yetkazilgan zarar va iqtisodiy yo‘qotishlar esa bu hisobga kirmagan. | USS Gerald R Ford supports Operation Epic Fury (998160).webm | Public domain | cut |
| 31 | 02:24.00–02:33.70 | Endi urushning eng xavfli jabhasiga o‘tamiz. Fors ko‘rfazi. Eron bilan ittifoqdosh Yaman husiylari 19-noyabr kuni Riyodga raketa zarbasi … | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | flash |
| 32 | 02:33.70–02:38.10 | Zarba Saudiya Arabistoni Suveren boylik fondining shtab-kvartirasi joylashgan, | KAFD 58.jpg | CC0 | dissolve |
| 33 | 02:38.10–02:40.80 | shaharning eng baland binalaridan biriga tegdi. | KAFD 46.jpg | CC0 | cut |
| 34 | 02:40.80–02:45.90 | Saudiya fuqaro muhofazasi xizmatiga ko‘ra, binaga zarar yetgan, lekin jabrlanganlar yo‘q. | KAFD 10.jpg | CC0 | dissolve |
| 35 | 02:45.90–02:50.20 | Bu Riyoddagi moliyaviy tumanga ikki hafta ichida berilgan ikkinchi zarba. | KAFD 13.jpg | CC0 | cut |
| 36 | 02:50.20–02:53.80 | 20-noyabr kuni husiylar yanada keskin bayonot berdi. | Houthis protest against airstrikes 2.png | Public domain | flash |
| 37 | 02:53.80–03:00.70 | Ular odamlarni Riyoddagi Qirol Abdulla moliyaviy tumanidan uzoqroq turishga chaqirib, uni harbiy nishon deb e’lon qildi. | KAFD 12.jpg | CC0 | cut |
| 38 | 03:00.70–03:06.50 | Shuningdek, aviakompaniyalarni Saudiya havo hududining katta qismi xavfli ekani haqida ogohlantirdi. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 39 | 03:06.50–03:11.80 | Saudiya boshchiligidagi koalitsiya esa Yamanning Hudayda shahri aholisini evakuatsiya qilishga chaqirdi. | Al Hudaydah - panoramio (959).jpg | CC BY 3.0 | dissolve |
| 40 | 03:11.80–03:14.30 | Hormuz bo‘g‘ozida ham vaziyat tinch emas. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 41 | 03:14.30–03:19.75 | Eron Inqilob qo‘riqchilari korpusi yana ikkita neft tankeri minaga urilib yonib ketganini da’vo qildi. | U S Forces Enforce Blockade (1016268).webm | Public domain | cut |
| 42 | 03:19.75–03:23.20 | Biroq bu da’vo mustaqil manbalar tomonidan tasdiqlanmagan. | U S Forces Start Mine Clearance Mission in Strait of Hormuz (9609002). | Public domain | cut |
| 43 | 03:23.20–03:28.90 | CBS News bunday da’volar deyarli har kuni aytilishini, lekin kamdan kam tasdiqlanishini ta’kidlaydi. | U S Forces Enforce Blockade (1016268).webm | Public domain | cut |
| 44 | 03:28.90–03:37.70 | Eron qo‘mondoni Abdurahim Musaviy shunday ogohlantirdi: «Agar ular infratuzilmaga zarba bersa, biz ham albatta ularning infratuzilmasiga … | Attack on areas north of Tehran 1 Avash 20 esfand 1404.webp | CC BY 4.0 | dissolve |
| 45 | 03:37.70–03:41.00 | Xo‘sh, bularning barchasi bizga qanday aloqasi bor? | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | flash |
| 46 | 03:41.00–03:42.90 | Birinchidan, neft narxi. | Gas prices on May 10, 2026 in Eugene, Oregon.jpg | CC BY 4.0 | cut |
| 47 | 03:42.90–03:53.45 | Reuters ma’lumotiga ko‘ra, 20-noyabr kuni Brent neftining bir barreli taxminan 92,5 dollar atrofida savdo qilindi. Urushdan oldin bu narx… | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 48 | 03:53.45–03:56.10 | Neft qimmatlashsa, butun dunyada yoqilg‘i, | Oil shortages in Thailand - "out of diesel" at a petrol station (2026- | CC BY 4.0 | dissolve |
| 49 | 03:56.10–03:58.90 | yuk tashish va oziq-ovqat narxlari ham oshib boradi. | Gas prices in Chula Vista, CA on 2026-09-29.jpg | CC0 | cut |
| 50 | 03:58.90–04:01.30 | Bu O‘zbekistonni ham chetlab o‘tmaydi. | Tashkent Uzbekistan aeroport.jpg | CC BY 4.0 | cut |
| 51 | 04:01.30–04:03.70 | Ikkinchidan, transport va safarlar. | Boeing 767-300ER UK67007 Uzbekistan Airways. Moscow 01.08.2025.jpg | CC0 | flash |
| 52 | 04:03.70–04:12.10 | Fors ko‘rfazi mamlakatlari O‘zbekiston fuqarolari uchun muhim yo‘nalish. Bu — ish, savdo, tranzit parvozlar va umra ziyoratlari demakdir. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 53 | 04:12.10–04:18.00 | Husiylarning Saudiya havo hududi haqidagi ogohlantirishi aviakompaniyalarning qarorlariga ta’sir qilishi mumkin. | Grounded airliners at Manchester Airport Feb 2026.jpg | CC BY 4.0 | dissolve |
| 54 | 04:18.00–04:26.10 | Hozircha parvozlar bekor qilingani haqida rasmiy xabar yo‘q, lekin ziyorat yoki safarga otlanganlar vaziyatni diqqat bilan kuzatib borish… | کاروان عمره دانشگاهیان 11 (Mehr, 2025).jpg | CC BY 4.0 | dissolve |
| 55 | 04:26.10–04:40.60 | Uchinchidan, mintaqaviy xavfsizlik. Eron Markaziy Osiyoning yaqin qo‘shnisi va janubiy dengiz yo‘llariga chiqishda muhim yo‘nalish. Urush… | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | flash |
| 56 | 04:40.60–04:44.00 | Endi eng muhim savol: bundan keyin nima bo‘ladi? | CENTCOM Completes Strikes on IRGC Targets in Iran (1021498).webm | Public domain | flash |
| 57 | 04:44.00–04:57.80 | Hozircha ikki ssenariy bor. Birinchisi: Tramp aytganidek, yangi yilgacha katta qaror qabul qilinmaydi va diplomatiyaga vaqt qoladi. Ikkin… | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 58 | 04:57.80–05:02.30 | Qaysi biri amalga oshishini hozir hech kim aniq ayta olmaydi. Faqat bir narsa aniq. | USS Gerald R Ford supports Operation Epic Fury (998160).webm | Public domain | cut |
| 59 | 05:02.30–05:07.50 | Saudiya Arabistoni husiylarga qarshi barcha zarur choralarni ko‘rish huquqini saqlab qolishini aytgan. | KAFD 18.jpg | CC0 | dissolve |
| 60 | 05:07.50–05:11.30 | Eron esa infratuzilmaga zarba berilsa, javob qaytarishini aytmoqda. | Attack on areas north of Tehran 14 Avash 20 esfand 1404.webp | CC BY 4.0 | cut |
| 61 | 05:11.30–05:16.60 | Bu esa har qanday yangi zarba butun ko‘rfazga yoyilishi mumkinligini anglatadi. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dissolve |
| 62 | 05:16.60–05:23.30 | Xulosa qilsak, bugun dunyo «shoshilmayapman» degan bayonot bilan zarba ehtimoli ortmoqda degan xabar o‘rtasida turibdi. | President Donald J. Trump on the United States Military Major Combat O | Public domain | flash |
| 63 | 05:23.30–05:25.20 | Urush o‘zining to‘qqizinchi oyiga kirdi. | U S B-1 bombers take off to support Operation Epic Fury (997873).webm | Public domain | cut |
| 64 | 05:25.20–05:28.70 | Uning narxini esa nafaqat front chizig‘idagilar, balki | Epic Fury Strike compilation (997841).webm | Public domain | cut |
| 65 | 05:28.70–05:30.60 | yoqilg‘i quyish shoxobchasi navbatidagi | Oil shortages in Thailand - "out of diesel" at a petrol station (2026- | CC BY 4.0 | cut |
| 66 | 05:30.60–05:33.60 | va aeroportdagi oddiy odamlar ham to‘lamoqda. | Grounded airliners at Manchester Airport Feb 2026.jpg | CC BY 4.0 | cut |
| 67 | 05:33.60–05:42.00 | Siz qanday o‘ylaysiz? Yangi yil Yaqin Sharqqa tinchlik olib keladimi yoki bu shunchaki yangi bo‘ron oldidan sukunatmi? | KC-135 Stratotanker refuels Fighter Aircraft during Operation Epic Fur | Public domain | dissolve |
| 68 | 05:42.00–05:47.90 | Fikringizni izohlarda yozib qoldiring. Voqealar rivojini kuzatib borish uchun kanalga obuna bo‘ling. | Motion graphics / xarita | Tahririyat grafikasi (Natural Earth — PD) | dip |
