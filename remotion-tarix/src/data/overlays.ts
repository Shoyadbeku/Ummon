// ======= MOTION GRAPHICS ELEMENTLARI =======
// Har bir element ovozdagi gapga bog'langan: seg = scripts/narration.txt qator raqami (0 dan),
// word = shu gapdagi so'z (ixtiyoriy) — element aynan shu so'z aytilganda chiqadi.
export type At = {seg: number; word?: string; delay?: number};

export type Overlay =
  | {type: 'lowerThird'; at: At; name: string; role: string; dur?: number}
  | {type: 'location'; at: At; place: string; country: string; coords: string; dur?: number}
  | {type: 'stat'; at: At; value: number; suffix?: string; label: string; sub?: string; dur?: number}
  | {type: 'keyword'; at: At; text: string; color?: string; dur?: number}
  | {type: 'stamp'; at: At; text: string; sub?: string; dur?: number}
  | {type: 'versus'; at: At; untilSeg: number; left: {image: string; title: string; sub: string}; right: {image: string; title: string; sub: string}}
  | {type: 'question'; at: At; title: string; a: string; b: string; cta: string};

export const OVERLAYS: Overlay[] = [
  {type: 'location', at: {seg: 1, word: 'Nyu-York'}, place: 'Nyu-York', country: 'Amerika Qo‘shma Shtatlari', coords: '40.7527° N · 73.9936° W'},
  {type: 'stat', at: {seg: 2, word: '3327-raqamli'}, value: 3327, label: 'XONA', sub: 'New Yorker mehmonxonasi · 33-qavat'},
  {type: 'stat', at: {seg: 3}, value: 86, label: 'YOSH', sub: '1856 — 1943'},
  {type: 'stat', at: {seg: 8, word: 'patentlarga'}, value: 300, suffix: '+', label: 'PATENT', sub: 'Dunyoning turli davlatlarida'},
  {type: 'lowerThird', at: {seg: 9, word: 'Nikola'}, name: 'Nikola Tesla', role: 'Ixtirochi · 1856–1943'},
  {type: 'keyword', at: {seg: 13}, text: 'NEGA?', dur: 1.6},
  {type: 'keyword', at: {seg: 17, word: '«o‘lim'}, text: 'O‘LIM NURI', color: '#e0523a'},
  {type: 'location', at: {seg: 24, word: 'Smilyan'}, place: 'Smilyan', country: 'Bugungi Xorvatiya', coords: '44.5653° N · 15.3125° E'},
  {type: 'versus', at: {seg: 38}, untilSeg: 40,
    left: {image: 'images/14_Tomas_Edison_va_ozgarmas_tok.jpg', title: 'TOMAS EDISON', sub: 'O‘zgarmas tok (DC)'},
    right: {image: 'images/15_Tesla_va_ozgaruvchan_tok_chizmalari.jpg', title: 'NIKOLA TESLA', sub: 'O‘zgaruvchan tok (AC)'}},
  {type: 'lowerThird', at: {seg: 46, word: 'Vestingauz'}, name: 'Jorj Vestingauz', role: 'Sanoatchi · Westinghouse Electric'},
  {type: 'location', at: {seg: 61, word: 'Long-Aylend'}, place: 'Long-Aylend', country: 'Nyu-York shtati, AQSh', coords: '40.9500° N · 72.8900° W'},
  {type: 'lowerThird', at: {seg: 66, word: 'Jon'}, name: 'Jon Pirpont Morgan', role: 'Moliyachi · bankir'},
  {type: 'stamp', at: {seg: 71, word: 'buzib'}, text: 'BUZILDI', sub: '1917'},
  {type: 'keyword', at: {seg: 85, word: '«teleforce»'}, text: 'TELEFORCE', color: '#7fc8ff'},
  {type: 'keyword', at: {seg: 89}, text: 'O‘LIM NURI', color: '#e0523a'},
  {type: 'stamp', at: {seg: 102, word: 'davlat'}, text: 'MAXFIY', sub: 'DAVLAT NAZORATIDA'},
  {type: 'stamp', at: {seg: 104, word: 'FBI'}, text: 'FBI', sub: 'FEDERAL QIDIRUV BYUROSI'},
  {type: 'lowerThird', at: {seg: 106, word: 'Alien'}, name: 'Alien Property Custodian', role: 'AQSh davlat idorasi'},
  {type: 'lowerThird', at: {seg: 112, word: 'Jon'}, name: 'Jon G. Tramp', role: 'MIT · elektrotexnika mutaxassisi'},
  {type: 'stamp', at: {seg: 120, word: 'tasdiqlamagan.'}, text: 'TASDIQLANMADI', sub: 'SUPERQUROL'},
  {type: 'keyword', at: {seg: 129, word: 'Bu'}, text: 'TARIXIY FAKT', color: '#d9a441', dur: 2},
  {type: 'location', at: {seg: 131, word: 'Belgraddagi'}, place: 'Belgrad', country: 'Serbiya · Nikola Tesla muzeyi', coords: '44.8048° N · 20.4710° E'},
  {type: 'keyword', at: {seg: 135, word: 'paradoks'}, text: 'PARADOKS', dur: 2},
  {type: 'question', at: {seg: 158}, title: 'Teslaning eng buyuk merosi', a: 'Haqiqiy ixtirolari', b: 'Amalga oshmagan orzulari', cta: 'Fikringizni izohlarda yozing'},
];
