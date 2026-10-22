export const FPS = 30;
export const DURATION = 47.0;

export const f = (s: number) => Math.round(s * FPS);

// Ovoz vaqt chizig'i bo'yicha kadrlar. `src` — klipdagi boshlanish soniyasi,
// `rate` — tezlik: klipdagi lab harakati ovozdagi so'zlarga tushishi uchun tanlangan.
// `cut: true` — yangi sahna (flesh, zoom-punch, whoosh).
export type Shot = {clip: number; from: number; to: number; src: number; rate: number; cut: boolean};

export const SHOTS: Shot[] = [
  {clip: 1, from: 0.0, to: 4.0, src: 3.95, rate: 1.0, cut: true},
  {clip: 1, from: 4.0, to: 8.6, src: 0.0, rate: 0.87, cut: true},
  {clip: 2, from: 8.6, to: 12.1, src: 0.0, rate: 1.0, cut: true},
  {clip: 2, from: 12.1, to: 15.4, src: 5.5, rate: 0.758, cut: true},
  {clip: 3, from: 15.4, to: 22.66, src: 0.8, rate: 0.758, cut: true},
  {clip: 4, from: 22.66, to: 25.5, src: 0.0, rate: 1.074, cut: true},
  {clip: 4, from: 25.5, to: 28.97, src: 3.05, rate: 0.896, cut: false},
  {clip: 4, from: 28.97, to: 34.1, src: 6.16, rate: 0.749, cut: false},
  {clip: 5, from: 34.1, to: 39.6, src: 0.0, rate: 0.764, cut: true},
  {clip: 5, from: 39.6, to: 45.4, src: 4.2, rate: 0.759, cut: false},
  {clip: 5, from: 45.4, to: 47.0, src: 8.6, rate: 0.875, cut: false},
];

// Ovozdagi gaplar (Whisper vaqtlari bo'yicha).
export const LINES: {start: number; end: number; text: string}[] = [
  {start: 0.0, end: 1.8, text: 'Yana tish pastam tugab qoldi!'},
  {start: 2.04, end: 3.88, text: 'Har ikki haftada yangisini olaman!'},
  {start: 4.18, end: 8.4, text: 'He-he! Tishlarim oppoq bo‘lishi uchun cho‘tkaning ustini to‘ldirib surtaman!'},
  {start: 8.98, end: 11.8, text: 'Xuddi televizordagi reklamalardagidek, to‘g‘rimi?'},
  {start: 12.18, end: 15.18, text: 'Ha-da! Ko‘proq ko‘pirsa, yaxshiroq tozalaydi!'},
  {start: 15.66, end: 20.98, text: 'Bilasanmi, stomatologlar tish pasta qutisidagi eng katta yolg‘on nima ekanligini aytishadi?'},
  {start: 21.28, end: 22.66, text: 'Qanaqa yolg‘on?'},
  {start: 22.66, end: 25.3, text: 'Chunki tozalash uchun bitta no‘xatdek pasta yetadi!'},
  {start: 25.66, end: 28.86, text: 'Lekin pastang bir oyda emas, bir haftada tugashi uchun,'},
  {start: 29.08, end: 33.86, text: 'reklamalarda cho‘tkaning butun uzunligi bo‘ylab pasta siqib ko‘rsatishadi!'},
  {start: 34.24, end: 38.04, text: 'Sen yoqtirgan o‘sha qalin ko‘pik esa — arzon kimyoviy modda!'},
  {start: 38.36, end: 39.2, text: 'SLS.'},
  {start: 39.8, end: 41.72, text: 'Hih, u tishni oqartirmaydi!'},
  {start: 42.06, end: 45.32, text: 'Shunchaki og‘zingda tozalik illyuziyasini yaratadi, xolos!'},
];

export type CalloutKind =
  | 'hook'
  | 'tag'
  | 'badge'
  | 'question'
  | 'pea'
  | 'month'
  | 'stamp'
  | 'sls'
  | 'cross'
  | 'illusion'
  | 'outro';

export const CALLOUTS: {kind: CalloutKind; from: number; to: number; title?: string; sub?: string; top?: number}[] = [
  {kind: 'hook', from: 0.0, to: 3.95, title: 'TISH PASTASI', sub: 'reklamasi siri'},
  {kind: 'tag', from: 4.3, to: 8.5, title: '1-XATO', sub: 'To‘la cho‘tka pasta'},
  {kind: 'tag', from: 12.2, to: 15.3, title: '2-XATO', sub: 'Ko‘p ko‘pik = toza?'},
  {kind: 'badge', from: 15.7, to: 21.1, title: 'STOMATOLOGLAR', sub: 'nima deydi?'},
  {kind: 'question', from: 21.28, to: 22.66, title: 'YOLG‘ON?'},
  {kind: 'pea', from: 23.2, to: 25.6, title: 'NO‘XATDEK', sub: 'yetarli'},
  {kind: 'month', from: 25.7, to: 28.95, title: '1 OY', sub: '1 HAFTA'},
  {kind: 'stamp', from: 29.1, to: 34.0, title: 'REKLAMA HIYLASI'},
  {kind: 'tag', from: 34.3, to: 38.25, title: 'QALIN KO‘PIK', sub: '= arzon kimyo', top: 1090},
  {kind: 'sls', from: 38.3, to: 39.75, title: 'SLS', sub: 'natriy laurilsulfat'},
  {kind: 'cross', from: 39.85, to: 41.9, title: 'OQARTIRMAYDI'},
  {kind: 'illusion', from: 42.06, to: 45.4, title: 'TOZALIK', sub: 'illyuziyasi'},
  {kind: 'outro', from: 45.4, to: 47.0, title: 'Do‘stlaringizga ulashing!', sub: 'OBUNA BO‘LING'},
];
