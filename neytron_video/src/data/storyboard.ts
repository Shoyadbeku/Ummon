import {Scene} from './types';
import {SRC} from './sources';

/**
 * One entry per sentence/idea of the original narration. Times are narration seconds
 * (Whisper segment starts). Every person shown is the person being talked about; where
 * no licensed real footage exists (Kim Jong-nam, the two women, the attack itself, Jang
 * Song-thaek) the scene is a labelled graphic, never a stand-in.
 */
const KL: [number, number] = [101.69, 3.14];
const PY = {name: 'Pxenyan', lon: 125.75, lat: 39.03};
const KLp = {name: 'Kuala-Lumpur', lon: 101.71, lat: 2.74, main: true};
const MAC = {name: 'Makao', lon: 113.54, lat: 22.19};

export const SCENES: Scene[] = [
  // ── HOOK ─────────────────────────────────────────────
  {start: 0, end: 2.43, v: {kind: 'photo', file: 'media/vost_close.jpg', move: {s0: 1.08, s1: 1.22, x0: -4, x1: -8}}, source: SRC.kremlin2023, note: 'Hook: real close-up of Kim Jong-un as his name is spoken'},
  {start: 2.43, end: 5.1, v: {kind: 'card', kicker: 'Hujjatli tergov', title: 'Aka o‘limi va hokimiyat uchun kurash', tone: 'red'}, note: 'Title card on "akasining o‘limi va hokimiyat uchun kurash"'},
  {start: 5.1, end: 8.6, v: {kind: 'date', date: '13.02.2017', place: 'Malayziya'}, note: 'Exact date and country as spoken'},
  {start: 8.6, end: 11.32, v: {kind: 'photo', file: 'media/klia2_aerial.jpg', move: {s0: 1.05, s1: 1.18, x1: -2}}, source: SRC.klia2aerial, lower: {name: 'KLIA2', role: 'Kuala-Lumpur xalqaro aeroporti, 2-terminal'}, note: 'The real airport (KLIA2 terminal where the attack took place)'},
  {start: 11.32, end: 15.94, v: {kind: 'photo', file: 'media/klia2_terminal.jpg', move: {s0: 1.04, s1: 1.14, x0: 1, x1: -1}}, source: SRC.klia2terminal, note: 'Terminal with passengers — same terminal'},
  {start: 15.94, end: 19.92, v: {kind: 'photo', file: 'media/klia2_checkin.jpg', move: {s0: 1.18, s1: 1.06}}, source: SRC.klia2checkin, note: 'Self check-in kiosks at KLIA2 — the area of the attack'},
  {start: 19.92, end: 33.02, v: {kind: 'cctv', title: 'KLIA2 · ro‘yxatdan o‘tish zali', lines: ['Erkak terminal bo‘ylab yuradi', 'Ikki ayol unga yaqinlashadi', 'Yuziga qo‘l tekkiziladi', 'Bir necha soniya — ayollar ketadi']}, note: 'No licensed CCTV exists — labelled schematic reconstruction'},
  {start: 33.02, end: 43.22, v: {kind: 'cctv', title: 'Keyingi daqiqalar', lines: ['Ahvoli yomonlashadi', 'Aeroport xodimlaridan yordam so‘raydi', 'Shifokorlar qutqarishga ulgurmaydi']}, note: 'Reconstruction continues: help desk, death'},
  {start: 43.22, end: 50.78, v: {kind: 'map', center: [108, 12], scale0: 900, scale1: 1500, pins: [KLp], caption: 'DUNYO E’TIBORI — MALAYZIYA'}, note: '"butun dunyo e’tibori Malayziyaga qaratildi" — map zoom to Malaysia'},
  {start: 50.78, end: 56.2, v: {kind: 'tree', focus: ['jongun', 'jongnam']}, source: SRC.tree, note: 'Kim Jong-un → his half-brother Kim Jong-nam (no licensed photo of Kim Jong-nam: silhouette node)'},
  {start: 56.2, end: 63.16, v: {kind: 'molecule'}, note: 'VX nerve agent — original molecule graphic'},
  {start: 63.16, end: 68.28, v: {kind: 'photo', file: 'media/opcw.jpg', move: {s0: 1.03, s1: 1.12}}, source: SRC.opcw, lower: {name: 'OPCW', role: 'Kimyoviy qurollarni taqiqlash tashkiloti'}, note: 'Banned under the Chemical Weapons Convention — OPCW HQ'},
  {start: 68.28, end: 84.88, v: {kind: 'question', lines: ['Nega u Malayziyada yashirincha yurgan?', 'Ikki ayol kim edi?', 'Ular rejadan xabardormidi?', 'Kim manfaatdor edi?']}, note: 'The four questions, revealed as spoken'},
  {start: 84.88, end: 93.92, v: {kind: 'photo', file: 'media/kumsusan.jpg', move: {s0: 1.03, s1: 1.15}}, source: SRC.kumsusan, lower: {name: 'Kumsusan saroyi', role: 'Pxenyan · Kimlar sulolasi maqbarasi'}, note: '"Shimoliy Koreyadagi hokimiyat ... Kimlar oilasi" — the Kim family mausoleum in Pyongyang'},
  {start: 93.92, end: 99.94, v: {kind: 'card', kicker: 'Manbalar', title: 'Real hodisalar · sud jarayonlari · jurnalistik surishtiruvlar'}, note: 'Statement of sourcing'},
  // ── KIM DYNASTY ──────────────────────────────────────
  {start: 99.94, end: 106.22, v: {kind: 'map', center: [127.5, 38.5], scale0: 2600, scale1: 3400, pins: [{...PY, main: true}, {name: 'Seul', lon: 126.98, lat: 37.57}], caption: '1948 · KOREYA XALQ DEMOKRATIK RESPUBLIKASI'}, note: 'Korean peninsula, northern part — DPRK 1948'},
  {start: 106.22, end: 111.76, v: {kind: 'photo', file: 'media/f1948_podium.jpg', fit: 'contain', move: {s0: 1, s1: 1.08}}, source: SRC.film1948, lower: {name: 'Kim Ir Sen', role: 'KXDR asoschisi · 1948–1994'}, note: 'Real 1948 film of Kim Il-sung'},
  {start: 111.76, end: 114.54, v: {kind: 'photo', file: 'media/kim_il_sung_1946.jpg', fit: 'contain', move: {s0: 1.0, s1: 1.07}}, source: SRC.kis1946, note: 'Kim Il-sung building a centralised system — 1946 rally speech'},
  {start: 114.54, end: 116.58, v: {kind: 'photo', file: 'media/kim_il_sung_1950.jpg', fit: 'contain', move: {s0: 1.0, s1: 1.05}}, source: SRC.kis1950, note: 'Kim Il-sung (died 1994) — authentic portrait'},
  {start: 116.58, end: 122.68, v: {kind: 'photo', file: 'media/kim_jong_il_2011.jpg', fit: 'contain', move: {s0: 1.0, s1: 1.1}}, source: SRC.kremlin2011, lower: {name: 'Kim Chen Ir', role: 'KXDR rahbari · 1994–2011'}, note: 'Power passes to Kim Jong-il — real photo'},
  {start: 122.68, end: 131.34, v: {kind: 'tree', focus: ['jongil', 'jongnam']}, source: SRC.tree, note: 'Kim Jong-il’s children; Kim Jong-nam born 1971, eldest son'},
  {start: 131.34, end: 141.14, v: {kind: 'card', kicker: 'Kim Chen Nam', title: 'To‘ng‘ich o‘g‘il — ehtimoliy voris', sub: 'Uzoq yillar xalqaro kuzatuvchilar shunday deb hisoblagan'}, note: 'Heir-apparent claim; no licensed photo of Kim Jong-nam exists'},
  {start: 141.14, end: 146.3, v: {kind: 'map', center: [137, 35.5], scale0: 2200, scale1: 3000, pins: [{name: 'Tokio', lon: 139.69, lat: 35.68, main: true}], caption: '2001 · YAPONIYA'}, note: '2001, Japan, fake passport'},
  {start: 146.3, end: 152.32, v: {kind: 'photo', file: 'media/disneyland.jpg', move: {s0: 1.05, s1: 1.16, x0: -1, x1: 1}}, source: SRC.disney, lower: {name: 'Tokyo Disneyland', role: 'U borishni rejalashtirgan ko‘ngilochar bog‘'}, note: 'The real Tokyo Disneyland'},
  {start: 152.32, end: 157.6, v: {kind: 'card', kicker: '2001', title: 'Yaponiyadan chiqarib yuborildi', sub: 'Voqea xalqaro matbuotda katta shov-shuvga sabab bo‘ldi'}, note: 'Deportation'},
  {start: 157.6, end: 164.4, v: {kind: 'photo', file: 'media/macau.jpg', move: {s0: 1.04, s1: 1.14, x0: 2, x1: -2}}, source: SRC.macau, lower: {name: 'Makao', role: 'Kim Chen Nam ko‘p yillar yashagan joy'}, note: 'Macau, where he lived'},
  {start: 164.4, end: 169.22, v: {kind: 'photo', file: 'media/vost_car.jpg', move: {s0: 1.05, s1: 1.18, x0: 4, x1: 6}}, source: SRC.kremlin2023, lower: {name: 'Kim Chen In', role: 'Kim Chen Irning kenja o‘g‘li'}, note: 'Younger brother Kim Jong-un comes forward — real photo'},
  {start: 169.22, end: 172.3, v: {kind: 'timeline', items: [{year: '1948', label: 'KXDR'}, {year: '1994', label: 'Kim Ir Sen vafoti'}, {year: '2001', label: 'Yaponiya'}, {year: '2011', label: 'Kim Chen Ir vafoti'}, {year: '2013', label: 'Chan Son Tek'}, {year: '2017', label: 'KLIA2'}], active: 3}, note: '2011: Kim Jong-il dies'},
  {start: 172.3, end: 175.34, v: {kind: 'photo', file: 'media/kim_putin_2019.jpg', move: {s0: 1.7, s1: 1.85, x0: 7, x1: 7, y0: 4, y1: 5}}, source: SRC.kremlin2019, lower: {name: 'Kim Chen In', role: '2011-yildan KXDR rahbari'}, note: 'New leader Kim Jong-un — real photo'},
  {start: 175.34, end: 188.58, v: {kind: 'card', kicker: 'Kim Chen Nam', title: 'Ochiq kurash boshlamadi', sub: 'Ammo jurnalistlarga hokimiyatning oilaviy meros sifatida o‘tishini tanqid qilgan'}, note: 'His public criticism of dynastic succession'},
  {start: 188.58, end: 192.36, v: {kind: 'photo', file: 'media/macau.jpg', move: {s0: 1.2, s1: 1.1, x0: -3, x1: 0}}, source: SRC.macau, note: 'Life abroad (Macau) while questions grew'},
  {start: 192.36, end: 201.34, v: {kind: 'tree', focus: ['jongil', 'jongnam', 'jongun']}, source: SRC.tree, note: 'Same father, different mothers'},
  {start: 201.34, end: 207.18, v: {kind: 'photo', file: 'media/vost_crowd.jpg', move: {s0: 1.04, s1: 1.16}}, source: SRC.kremlin2023, note: 'Kim Jong-un with his military entourage — consolidates power (real photo)'},
  {start: 207.18, end: 222.96, v: {kind: 'map', center: [115, 22], scale0: 650, scale1: 820, pins: [PY, MAC, KLp], arcs: [['Pxenyan', 'Makao']], caption: 'XORIJDAGI HAYOT'}, note: 'Kim Jong-nam abroad; potential alternative leader'},
  {start: 222.96, end: 234.58, v: {kind: 'split', left: {file: 'media/kim_il_sung_1950.jpg', name: 'Kim Ir Sen'}, right: {file: 'media/kim_jong_il_2011.jpg', name: 'Kim Chen Ir'}, mid: 'OTA → O‘G‘IL'}, source: {label: 'Arxiv (c. 1950) · Kremlin.ru (2011) / Wikimedia Commons', license: 'PD · CC BY 4.0'}, note: 'Power built around the Kim family — father and son, real photos'},
  {start: 234.58, end: 248.38, v: {kind: 'card', kicker: '2013', title: 'Chan Son Tek hibsga olinib, qatl etildi', sub: 'Kim Chen Inning amakisi · “davlatga xiyonat” ayblovi'}, note: 'No licensed photo of Jang Song-thaek — text card'},
  {start: 248.38, end: 254.84, v: {kind: 'photo', file: 'media/vost_close.jpg', fit: 'contain', move: {s0: 1.0, s1: 1.06}}, source: SRC.kremlin2023, note: 'Tight control under Kim Jong-un — real photo'},
  {start: 254.84, end: 270.58, v: {kind: 'card', kicker: 'Ochiq ma’lumot', title: 'Juda cheklangan', sub: 'Tahlilchilar taxminlari buyruqni kim berganini isbotlamaydi'}, note: 'Explicitly marks analyst speculation as unproven'},
  // ── 13 FEBRUARY 2017 ─────────────────────────────────
  {start: 270.58, end: 277.44, v: {kind: 'map', center: [108, 13], scale0: 950, scale1: 1150, pins: [KLp, MAC], arcs: [['Kuala-Lumpur', 'Makao']], caption: '13.02.2017 · REJALASHTIRILGAN PARVOZ'}, note: 'Planned flight KL → Macau'},
  {start: 277.44, end: 282.36, v: {kind: 'photo', file: 'media/klia2_checkin.jpg', move: {s0: 1.06, s1: 1.2, x0: 2, x1: -2}}, source: SRC.klia2checkin, note: 'Check-in area where he was attacked'},
  {start: 282.36, end: 286.2, v: {kind: 'cctv', title: 'Kuzatuv kameralari', lines: ['Harakatlar kameralarga yozib olingan']}, note: 'CCTV existed but is not licensed — reconstruction card'},
  {start: 286.2, end: 290.56, v: {kind: 'card', kicker: 'Indoneziya fuqarosi', title: 'Siti Aisyah', tone: 'dark'}, note: 'No licensed photo — name card (Commons hits were different women)'},
  {start: 290.56, end: 297.62, v: {kind: 'card', kicker: 'Vyetnam fuqarosi', title: 'Doan Thi Huong', sub: 'Ikkalasi ham tez orada hibsga olindi'}, note: 'No licensed photo — name card'},
  {start: 297.62, end: 305.58, v: {kind: 'card', kicker: 'Tergov', title: 'Aldangan insonlar?', sub: 'Ayollar o‘zlarini ongli ishtirokchi emas deb tasvirlashdi', tone: 'red'}, note: 'Their defence'},
  {start: 305.58, end: 324.64, v: {kind: 'cctv', title: 'Ayollarning aytishicha', lines: ['Noma’lum erkaklar TV-hazil dasturini taklif qiladi', 'Begona odamlar yuziga “zararsiz” suyuqlik', 'Kim Chen Namga ham “navbatdagi hazil”']}, note: 'Their account of the "prank show" — reconstruction text'},
  {start: 324.64, end: 331.18, v: {kind: 'molecule'}, note: '"Bu VX nerv agenti edi"'},
  {start: 331.18, end: 341.48, v: {kind: 'photo', file: 'media/klia2_terminal.jpg', move: {s0: 1.18, s1: 1.06}}, source: SRC.klia2terminal, note: 'Medical clinic at the airport, died on the way to hospital'},
  {start: 341.48, end: 347.82, v: {kind: 'card', kicker: 'Sud-tibbiy ekspertiza', title: 'O‘lim sababi: VX bilan zaharlanish', tone: 'red'}, note: 'Forensic finding'},
  {start: 347.82, end: 357.98, v: {kind: 'card', kicker: 'VX', title: 'Dunyodagi eng xavfli nerv agentlaridan biri', sub: 'Asab tizimining normal ishlashini izdan chiqaradi'}, note: 'What VX does'},
  {start: 357.98, end: 368.14, v: {kind: 'photo', file: 'media/klia2_aerial.jpg', move: {s0: 1.2, s1: 1.05}}, source: SRC.klia2aerial, note: 'Public place: thousands of passengers'},
  {start: 368.14, end: 375.66, v: {kind: 'photo', file: 'media/opcw.jpg', move: {s0: 1.14, s1: 1.04, x0: -2, x1: 1}}, source: SRC.opcw, note: 'Chemical-weapons use → international dispute'},
  {start: 375.66, end: 388.16, v: {kind: 'map', center: [114, 22], scale0: 650, scale1: 760, pins: [KLp, PY], arcs: [['Kuala-Lumpur', 'Pxenyan']], caption: 'GUMONLANUVCHILAR MALAYZIYANI TARK ETDI'}, note: 'Suspects left Malaysia the same day'},
  {start: 388.16, end: 394.1, v: {kind: 'card', kicker: 'BMT', title: 'Ekspertlar ma’lumotlarni o‘rgandi'}, note: 'UN experts'},
  {start: 394.1, end: 402.8, v: {kind: 'card', kicker: '2018 · AQSh hukumati', title: '“KXDR Kim Chen Namni o‘ldirish uchun VX ishlatgan”', sub: 'Rasmiy xulosa'}, note: 'US government finding (2018)'},
  {start: 402.8, end: 406.32, v: {kind: 'card', kicker: 'Shimoliy Koreya', title: 'Aloqadorlikni rad etdi', tone: 'red'}, note: 'DPRK denial'},
  {start: 406.32, end: 413.68, v: {kind: 'question', lines: ['Suiqasdni kim rejalashtirgan?', 'Yakuniy buyruq qayerdan kelgan?']}, note: 'Open questions'},
  // ── THE TRIAL ────────────────────────────────────────
  {start: 413.68, end: 425.88, v: {kind: 'card', kicker: 'Shoh Olam oliy sudi · 2017', title: 'Ikki ayolga qotillik ayblovi', sub: 'Malayziya qonunchiligiga ko‘ra o‘lim jazosi xavfi'}, note: 'Charges and possible death penalty'},
  {start: 425.88, end: 431.5, v: {kind: 'card', kicker: 'Himoya', title: 'Ayollar aldangan, tashkilotchilar boshqalar'}, note: 'Defence argument'},
  {start: 431.5, end: 435.87, v: {kind: 'date', date: 'MART 2019', place: 'Kutilmagan qaror'}, note: 'March 2019'},
  {start: 435.87, end: 440.12, v: {kind: 'photo', file: 'media/id_letter.jpg', fit: 'contain', move: {s0: 1.0, s1: 1.12, y0: 4, y1: -4}}, source: SRC.idLetter, lower: {name: 'Siti Aisyah', role: 'Ayblov bekor qilindi, ozod etildi'}, note: 'Real Indonesian government letter requesting Siti Aisyah’s release'},
  {start: 440.12, end: 453.84, v: {kind: 'card', kicker: 'Doan Thi Huong', title: 'Ayblov yengillashtirildi', sub: 'Xavfli vosita bilan zarar yetkazishni tan oldi · keyinchalik ozod etildi'}, note: 'Doan Thi Huong plea'},
  {start: 453.84, end: 467.52, v: {kind: 'card', kicker: 'Natija', title: 'Hech kim qotillikda aybdor deb topilmadi', sub: 'Gumon qilingan KXDR fuqarolari sudda javob bermadi', tone: 'red'}, note: 'Outcome'},
  {start: 467.52, end: 487.24, v: {kind: 'question', lines: ['Ayollarni kim boshqargan?', 'Kimyoviy modda qayerdan kelgan?', 'Nega aynan Kuala-Lumpur?', 'Javob berilmadi.']}, note: 'Unanswered questions'},
  // ── ANALYSIS ─────────────────────────────────────────
  {start: 487.24, end: 499.86, v: {kind: 'photo', file: 'media/kumsusan.jpg', move: {s0: 1.2, s1: 1.06, x0: -3, x1: 0}}, source: SRC.kumsusan, lower: {name: 'Pxenyan', role: 'Janubiy Koreya va AQSh ayblovlari KXDRga qaratildi'}, note: 'Accusations toward the North Korean state — Pyongyang'},
  {start: 499.86, end: 512.22, v: {kind: 'photo', file: 'media/vost_car.jpg', move: {s0: 1.9, s1: 2.05, x0: 18, x1: 18, y0: 22, y1: 23}}, source: SRC.kremlin2023, note: 'Analyst views on the leadership — Kim Jong-un real photo (face crop)'},
  {start: 512.22, end: 516.24, v: {kind: 'card', kicker: 'Muhim', title: 'Shaxsan buyruq bergani sudda isbotlanmagan', tone: 'red'}, note: 'Unproven claim clearly labelled'},
  {start: 516.24, end: 525.84, v: {kind: 'question', lines: ['VX ishlatilgani — hujjatlashtirilgan', 'Kim Chen Nam o‘ldirilgani — hujjatlashtirilgan', 'KXDR fuqarolari tergov markazida — hujjatlashtirilgan']}, note: 'Documented facts'},
  {start: 525.84, end: 543.98, v: {kind: 'map', center: [114, 22], scale0: 650, scale1: 820, pins: [KLp, PY], caption: 'DIPLOMATIK INQIROZ'}, note: 'Malaysia–DPRK diplomatic crisis'},
  // ── EPILOGUE ─────────────────────────────────────────
  {start: 543.98, end: 553.24, v: {kind: 'tree', focus: ['jongnam', 'jongun']}, source: SRC.tree, note: 'Two brothers'},
  {start: 553.24, end: 557.0, v: {kind: 'photo', file: 'media/macau.jpg', move: {s0: 1.05, s1: 1.15}}, source: SRC.macau, note: 'The one who lived abroad'},
  {start: 557.0, end: 561.54, v: {kind: 'photo', file: 'media/klia2_checkin.jpg', move: {s0: 1.12, s1: 1.25}}, source: SRC.klia2checkin, note: 'Killed at the airport in 2017'},
  {start: 561.54, end: 576.38, v: {kind: 'timeline', items: [{year: '13.02.2017', label: 'Hujum'}, {year: '2017', label: 'Ayblov'}, {year: '2018', label: 'AQSh xulosasi'}, {year: '2019', label: 'Sud qarorlari'}, {year: 'Bugun', label: 'Savollar ochiq'}], active: 4}, note: 'Investigations, findings, trial, unresolved'},
  {start: 576.38, end: 581.48, v: {kind: 'photo', file: 'media/sgp_handshake.jpg', move: {s0: 1.05, s1: 1.15}}, source: SRC.whSingapore, lower: {name: 'Singapur, 2018', role: 'Davlat rahbarlarining rasmiy uchrashuvi'}, note: 'Official summit (Singapore 2018) — White House video frame'},
  {start: 581.48, end: 585.48, v: {kind: 'photo', file: 'media/sgp_walk.jpg', move: {s0: 1.1, s1: 1.2}}, source: SRC.whSingapore, note: 'Official summit — walk at Capella hotel'},
  {start: 585.48, end: 590.0, v: {kind: 'photo', file: 'media/dmz_handshake.jpg', move: {s0: 1.06, s1: 1.16}}, source: SRC.whDmz, lower: {name: 'DMZ, 2019', role: 'Rasmiy uchrashuv'}, note: 'Official meeting at the DMZ — White House video frame'},
  {start: 590.0, end: 603.44, v: {kind: 'tree', focus: ['jongnam'], dead: ['jongnam']}, source: SRC.tree, note: 'Kim Jong-nam: never leader, yet in history'},
  {start: 603.44, end: 613.32, v: {kind: 'question', lines: ['Ortida hokimiyat uchun kurash turganmi?', 'Yoki biz bilmagan sabablar bormi?', 'Fikringizni izohlarda yozing']}, note: 'Viewer question / CTA as spoken'},
  {start: 613.32, end: 626.71, v: {kind: 'card', kicker: 'Kim Chen Nam ishi', title: 'Yakuniy buyruqni kim bergani — hali aniqlanmagan', tone: 'red'}, note: 'Closing line'},
];
