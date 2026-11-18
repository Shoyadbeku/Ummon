// Word-level timings (seconds) from Whisper large-v3 (faster-whisper), manually corrected
// to standard Uzbek Latin spelling. kw = keyword that gets accent colour in captions.
export type Word = {w: string; s: number; e: number; kw?: boolean};

export const WORDS: Word[] = [
  {w: 'Bugun', s: 0.0, e: 0.48},
  {w: 'dunyoning', s: 0.48, e: 1.08},
  {w: 'eng', s: 1.08, e: 1.44, kw: true},
  {w: 'boy', s: 1.44, e: 1.66, kw: true},
  {w: 'odamlaridan', s: 1.66, e: 2.36},
  {w: 'biri', s: 2.36, e: 2.64},
  {w: "bo'lgan", s: 2.64, e: 3.02},
  {w: 'Ilon', s: 3.02, e: 3.34, kw: true},
  {w: 'Mask', s: 3.34, e: 3.84, kw: true},

  {w: 'bir', s: 3.84, e: 4.16},
  {w: 'paytlar', s: 4.16, e: 4.62},
  {w: "o'z", s: 4.62, e: 4.96},
  {w: 'kompaniyasida', s: 4.96, e: 5.68},
  {w: 'tunab', s: 5.68, e: 6.04, kw: true},
  {w: 'ishlaganini', s: 6.04, e: 6.6, kw: true},
  {w: 'bilasizmi?', s: 6.6, e: 7.1},

  {w: '1990-yillarda', s: 7.22, e: 8.98, kw: true},
  {w: 'u', s: 8.98, e: 9.22},
  {w: 'ukasi', s: 9.22, e: 9.7},
  {w: 'bilan', s: 9.7, e: 9.94},
  {w: 'Zip2', s: 9.94, e: 10.38, kw: true},
  {w: 'nomli', s: 10.38, e: 10.9},
  {w: 'internet', s: 10.9, e: 11.22},
  {w: 'kompaniyasini', s: 11.22, e: 12.08},
  {w: 'tashkil', s: 12.08, e: 12.42},
  {w: 'qilgan.', s: 12.42, e: 12.75},

  {w: 'Pulni', s: 12.8, e: 13.3},
  {w: 'tejash', s: 13.3, e: 13.64, kw: true},
  {w: 'uchun', s: 13.64, e: 14.0},
  {w: 'Mask', s: 14.0, e: 14.22},
  {w: "ba'zan", s: 14.22, e: 14.76},
  {w: 'ofisda', s: 14.76, e: 15.12, kw: true},
  {w: 'uxlagan,', s: 15.12, e: 15.62, kw: true},

  {w: 'dush', s: 15.68, e: 16.06, kw: true},
  {w: 'qabul', s: 16.06, e: 16.38},
  {w: 'qilishga', s: 16.38, e: 16.64},
  {w: 'esa', s: 16.64, e: 16.84},
  {w: 'sport', s: 16.84, e: 17.15, kw: true},
  {w: 'zaliga', s: 17.15, e: 17.48, kw: true},
  {w: 'borgan.', s: 17.48, e: 17.9},

  {w: '1999-yilda', s: 17.98, e: 19.84, kw: true},
  {w: 'Zip2', s: 19.84, e: 20.22},
  {w: 'qariyb', s: 20.22, e: 20.72},
  {w: '307', s: 20.72, e: 21.36, kw: true},
  {w: 'million', s: 21.36, e: 21.82, kw: true},
  {w: 'dollarga', s: 21.82, e: 22.2, kw: true},
  {w: 'sotildi.', s: 22.2, e: 22.64},

  {w: 'Ammo', s: 22.64, e: 23.22},
  {w: 'Mask', s: 23.22, e: 23.52},
  {w: 'shu', s: 23.52, e: 23.74},
  {w: 'yerda', s: 23.74, e: 23.98},
  {w: "to'xtamadi.", s: 23.98, e: 24.5, kw: true},

  {w: 'Keyinchalik', s: 24.56, e: 25.28},
  {w: 'u', s: 25.28, e: 25.44},
  {w: 'PayPal,', s: 25.44, e: 26.18, kw: true},
  {w: 'Tesla', s: 26.18, e: 26.56, kw: true},
  {w: 'va', s: 26.56, e: 26.9},
  {w: 'SpaceX', s: 26.9, e: 27.3, kw: true},
  {w: 'kabi', s: 27.3, e: 27.78},
  {w: 'kompaniyalar', s: 27.78, e: 28.3},
  {w: 'bilan', s: 28.3, e: 28.56},
  {w: "bog'liq", s: 28.56, e: 28.9},
  {w: 'ulkan', s: 28.9, e: 29.44, kw: true},
  {w: 'loyihalarga', s: 29.44, e: 30.08, kw: true},
  {w: 'kirishdi.', s: 30.08, e: 30.46},

  {w: 'Bir', s: 30.5, e: 31.02},
  {w: 'paytlar', s: 31.02, e: 31.42},
  {w: 'ofisda', s: 31.42, e: 31.8, kw: true},
  {w: 'uxlagan', s: 31.8, e: 32.3, kw: true},
  {w: 'yigit,', s: 32.3, e: 32.72},

  {w: 'keyinchalik', s: 32.72, e: 33.36},
  {w: 'kosmosga', s: 33.36, e: 33.88, kw: true},
  {w: 'raketalar', s: 33.88, e: 34.4, kw: true},
  {w: 'uchiradigan', s: 34.4, e: 34.9},
  {w: 'tadbirkorga', s: 34.9, e: 35.34, kw: true},
  {w: 'aylandi.', s: 35.34, e: 35.94},

  {w: 'Sizningcha,', s: 35.98, e: 36.82},
  {w: 'bu', s: 36.82, e: 36.98},
  {w: 'mehnat', s: 36.98, e: 37.5, kw: true},
  {w: 'natijasimi?', s: 37.5, e: 38.06},
  {w: 'Yoki', s: 38.06, e: 38.42},
  {w: 'daholik?', s: 38.42, e: 39.1, kw: true},
];

export type Page = {words: Word[]; s: number; e: number};

// Group words into short caption pages (max 3 words / ~18 chars, break on punctuation or pauses)
export const buildPages = (words: Word[]): Page[] => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) pages.push({words: cur, s: cur[0].s, e: cur[cur.length - 1].e});
    cur = [];
  };
  words.forEach((w, i) => {
    const next = words[i + 1];
    const len = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
    if (cur.length && (cur.length >= 3 || len > 18)) flush();
    cur.push(w);
    const punct = /[.,?!]$/.test(w.w);
    const gap = next ? next.s - w.e : 1;
    if (punct || gap > 0.25 || !next) flush();
  });
  // extend each page to the start of the next one so captions never flicker off mid-sentence
  for (let i = 0; i < pages.length - 1; i++) {
    const gap = pages[i + 1].s - pages[i].e;
    if (gap < 0.4) pages[i].e = pages[i + 1].s;
  }
  return pages;
};

export const PAGES = buildPages(WORDS);
