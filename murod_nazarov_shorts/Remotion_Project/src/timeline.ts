// Single source of truth for timing. All times are in seconds and come from the
// word-level transcription of the original voice (Whisper large-v3, hand-checked).
export const FPS = 30;
export const DURATION_S = 35.0; // voice is 34.51s; 0.5s tail for the music to breathe
export const f = (s: number) => Math.round(s * FPS);

// Corrected Uzbek transcript, word timings (start, end)
export const WORDS = {
  bugun: 0.0,
  toshkentda: 0.56,
  katta: 1.2,
  binolar: 1.56,
  qurayotgan: 2.02,
  murod: 2.52,
  nazarov: 2.94,
  birPaytlar: 3.54,
  yaponiyada: 4.28,
  tahsil: 4.92,
  bilarmidingiz: 5.76,
  u: 7.02,
  y1982: 7.62,
  toshkentda2: 9.18,
  tugilgan: 9.72,
  y14: 10.18,
  yoshida: 10.78,
  otasidan: 11.38,
  ayrilgan: 11.82,
  keyinchalik: 12.48,
  tdshi: 13.36,
  sharqshunoslik: 14.1,
  institutida: 14.76,
  va: 15.94,
  yaponiyaning: 16.32,
  tsukuba: 16.98,
  universitetida: 17.46,
  bugun2: 18.86,
  murad: 19.84,
  buildings: 20.4,
  kompaniyasi: 20.82,
  asoschisi: 21.34,
  sifatida: 22.0,
  uning: 23.34,
  oddiy: 24.26,
  savolni: 24.92,
  tugdiradi: 25.38,
  katta2: 26.02,
  biznes: 26.9,
  qurishUchun: 27.26,
  eng: 27.82,
  muhimi: 28.08,
  nima: 28.68,
  pul: 29.12,
  bilim: 30.0,
  yoki: 30.58,
  tavakkalchilik: 31.24,
  siz: 32.3,
  qaysiBirini: 32.96,
  tanlaysiz: 33.6,
} as const;

// Scene cut points (seconds)
export const SCENES = [
  {id: 'hook', from: 0.0, to: 1.2},
  {id: 'cranes', from: 1.2, to: 2.52},
  {id: 'name', from: 2.52, to: 3.6},
  {id: 'flag', from: 3.6, to: 4.8},
  {id: 'shibuya', from: 4.8, to: 6.95},
  {id: 'year', from: 6.95, to: 9.15},
  {id: 'globeTashkent', from: 9.15, to: 10.15},
  {id: 'father', from: 10.15, to: 11.3},
  {id: 'boy', from: 11.3, to: 12.45},
  {id: 'institute', from: 12.45, to: 14.8},
  {id: 'books', from: 14.8, to: 15.94},
  {id: 'flight', from: 15.94, to: 17.46},
  {id: 'tsukuba', from: 17.46, to: 18.85},
  {id: 'today', from: 18.85, to: 19.8},
  {id: 'brand', from: 19.8, to: 21.3},
  {id: 'founder', from: 21.3, to: 23.2},
  {id: 'question', from: 23.2, to: 25.95},
  {id: 'business', from: 25.95, to: 28.95},
  {id: 'money', from: 28.95, to: 29.9},
  {id: 'knowledge', from: 29.9, to: 30.7},
  {id: 'risk', from: 30.7, to: 32.25},
  {id: 'choice', from: 32.25, to: DURATION_S},
] as const;

export type SceneId = (typeof SCENES)[number]['id'];

// Sound design cues: [file, start second, volume]
export const SFX: Array<[string, number, number]> = [
  ['sfx_2782.wav', 0.0, 0.06], // trailer impact on the very first frame (hook)
  ['sfx_1491.wav', 0.98, 0.14], // whoosh into cranes
  ['sfx_1464.wav', 2.47, 0.18], // whoosh into name card
  ['sfx_2152.wav', 2.52, 0.14], // name slam
  ['sfx_1467.wav', 3.3, 0.18], // whoosh into Japan
  ['sfx_1478.wav', 4.65, 0.35], // quick accent
  ['sfx_2152.wav', 7.62, 0.13], // year counter lands
  ['sfx_2350.wav', 9.3, 0.5], // map pin pop
  ['sfx_1687.wav', 10.18, 0.13], // heartbeat impact: "14 yoshida"
  ['sfx_1491.wav', 12.25, 0.18], // whoosh into institute
  ['sfx_1474.wav', 15.5, 0.18], // tunnel woosh into the flight
  ['sfx_1464.wav', 17.42, 0.18],
  ['sfx_2908.wav', 19.0, 0.2], // big cinematic impact on "Murad Buildings"
  ['sfx_1467.wav', 21.1, 0.16],
  ['sfx_2902.wav', 24.7, 0.09], // reverse impact rising into the music drop at 26.0s
  ['sfx_2152.wav', 29.12, 0.15], // PUL
  ['sfx_2152.wav', 30.0, 0.15], // BILIM
  ['sfx_2152.wav', 31.24, 0.17], // TAVAKKALCHILIK
  ['sfx_1491.wav', 32.05, 0.18],
];
