// ======= SHABLON SOZLAMALARI — shu faylni o'zgartirib, yangi video qiling =======
export const VIDEO = {
  fps: 30,
  width: 1920,
  height: 1080,
  // Video sarlavhasi (boshida chiqadi)
  title: 'NIKOLA TESLA',
  subtitle: "Yashirilgan hujjatlar siri",
  // Kanal nomi (oxirgi kadrda)
  channel: 'Tarix sirlari',
  // Fayllar (public/ papkasida)
  voice: 'voice.mp3',
  music: 'music.mp3',
  // Musiqa balandligi: ovoz paytida va ovozsiz paytda
  musicVolume: 0.13,
  musicVolumeIntro: 0.35,
  // Ovozdan oldin intro (soniya) va oxirida end-card (soniya)
  introSeconds: 4,
  outroSeconds: 6,
  // Sahnalar orasidagi o'tish (kadr)
  transitionFrames: 18,
  // Ranglar
  accent: '#d9a441',
  text: '#f4ead6',
};

// Boblar: qaysi rasm raqamidan boshlanadi
export const CHAPTERS: {scene: number; label: string}[] = [
  {scene: 1, label: 'Muqaddima'},
  {scene: 9, label: 'I bob · Daho tug‘ilishi'},
  {scene: 14, label: 'II bob · Toklar urushi'},
  {scene: 24, label: 'III bob · Vordenklif orzusi'},
  {scene: 34, label: 'IV bob · «O‘lim nuri»'},
  {scene: 40, label: 'V bob · Yo‘qolgan hujjatlar'},
  {scene: 55, label: 'Xulosa'},
];

// Yil belgilari: rasm raqami -> [yil, izoh]
export const STAMPS: Record<number, [string, string]> = {
  1: ['1943', '7-yanvar · Nyu-York'],
  9: ['1856', '10-iyul · Smilyan qishlog‘i'],
  16: ['1884', 'Amerikaga kelish'],
  25: ['1901', 'Long-Aylend · Nyu-York'],
  29: ['1917', 'Minora buzib tashlandi'],
  34: ['1930', 'Yangi urush xavfi'],
  40: ['1943', 'New Yorker mehmonxonasi'],
  47: ['1943', 'Yanvar oxiri · tekshiruv'],
};
