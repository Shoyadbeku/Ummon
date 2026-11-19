export const FPS = 30;
export const W = 1080;
export const H = 1920;
export const DURATION_S = 32.0; // voice is 31.6 s
export const f = (s: number) => Math.round(s * FPS);

export type Tone = 'gold' | 'green' | 'red' | 'accent';
export type Word = {t: string; s: number; e: number; tone?: Tone};

// Word-level timings from Whisper large-v3 (word_timestamps), text corrected to standard Uzbek Latin.
export const WORDS: Word[] = [
  {t: 'Siz', s: 0.0, e: 0.24},
  {t: 'Shahzodani', s: 0.24, e: 1.0, tone: 'gold'},
  {t: 'taniysiz,', s: 1.0, e: 1.46},
  {t: 'lekin', s: 1.56, e: 2.12},
  {t: 'uning', s: 2.12, e: 2.34},
  {t: 'haqiqiy', s: 2.34, e: 2.8, tone: 'accent'},
  {t: 'ismini', s: 2.8, e: 3.2, tone: 'accent'},
  {t: 'bilasizmi?', s: 3.2, e: 3.62},
  {t: 'Oʻzbekistonning', s: 4.18, e: 4.98, tone: 'accent'},
  {t: 'eng', s: 4.98, e: 5.16},
  {t: 'mashhur', s: 5.16, e: 5.84, tone: 'gold'},
  {t: 'estrada', s: 5.84, e: 6.28},
  {t: 'yulduzlaridan', s: 6.28, e: 6.94, tone: 'gold'},
  {t: 'biri', s: 6.94, e: 7.12},
  {t: 'Shahzodaning', s: 7.12, e: 7.86, tone: 'gold'},
  {t: 'asl', s: 7.86, e: 8.22},
  {t: 'ismi', s: 8.22, e: 8.46},
  {t: 'Zilola', s: 8.46, e: 9.04, tone: 'green'},
  {t: 'Musayeva.', s: 9.04, e: 9.68, tone: 'green'},
  {t: 'U', s: 9.76, e: 10.24},
  {t: 'yakkaxon', s: 10.24, e: 10.8, tone: 'accent'},
  {t: 'ijodini', s: 10.8, e: 11.2},
  {t: 'boshlashdan', s: 11.2, e: 11.68},
  {t: 'oldin', s: 11.68, e: 12.02},
  {t: '«Jonim»', s: 12.04, e: 12.6, tone: 'gold'},
  {t: 'guruhida', s: 12.6, e: 12.94, tone: 'gold'},
  {t: 'qoʻshiq', s: 12.94, e: 13.18},
  {t: 'kuylagan,', s: 13.18, e: 13.56},
  {t: 'keyinchalik', s: 13.76, e: 14.5},
  {t: 'Shahzoda', s: 14.5, e: 15.18, tone: 'gold'},
  {t: 'taxallusi', s: 15.18, e: 15.66, tone: 'accent'},
  {t: 'bilan', s: 15.66, e: 15.9},
  {t: 'sahnaga', s: 15.9, e: 16.3},
  {t: 'chiqib,', s: 16.3, e: 16.56},
  {t: 'katta', s: 16.56, e: 17.08},
  {t: 'mashhurlikka', s: 17.08, e: 17.7, tone: 'gold'},
  {t: 'erishgan.', s: 17.7, e: 18.1},
  {t: 'Uning', s: 18.22, e: 18.86},
  {t: 'qoʻshiqlari', s: 18.86, e: 19.42, tone: 'accent'},
  {t: 'Oʻzbekistondan', s: 19.42, e: 20.36},
  {t: 'tashqarida', s: 20.36, e: 20.9, tone: 'gold'},
  {t: 'ham', s: 20.9, e: 21.14},
  {t: 'tinglovchilar', s: 21.14, e: 21.66, tone: 'accent'},
  {t: 'topgan.', s: 21.66, e: 22.02},
  {t: 'Eng', s: 22.2, e: 22.64},
  {t: 'qizigʻi,', s: 22.64, e: 23.02, tone: 'accent'},
  {t: 'millionlab', s: 23.08, e: 23.84, tone: 'gold'},
  {t: 'odamlar', s: 23.84, e: 24.28},
  {t: 'uni', s: 24.28, e: 24.52},
  {t: 'tugʻilgandagi', s: 24.52, e: 25.28},
  {t: 'ismi', s: 25.28, e: 25.56},
  {t: 'bilan', s: 25.56, e: 25.8},
  {t: 'emas,', s: 25.8, e: 26.0, tone: 'red'},
  {t: 'sahnadagi', s: 26.12, e: 26.94},
  {t: 'taxallusi', s: 26.94, e: 27.48, tone: 'gold'},
  {t: 'bilan', s: 27.48, e: 27.74},
  {t: 'taniydi.', s: 27.74, e: 28.23},
  {t: 'Sizningcha,', s: 28.62, e: 29.08},
  {t: 'Shahzodaning', s: 29.08, e: 29.96, tone: 'gold'},
  {t: 'eng', s: 29.96, e: 30.14},
  {t: 'zoʻr', s: 30.14, e: 30.5, tone: 'accent'},
  {t: 'qoʻshigʻi', s: 30.5, e: 30.86},
  {t: 'qaysi?', s: 30.86, e: 31.4, tone: 'accent'},
];

// Caption pages: max 3 words / 20 chars, always break after punctuation.
export type Page = {words: Word[]; s: number; e: number};
export const PAGES: Page[] = (() => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) pages.push({words: cur, s: cur[0].s, e: cur[cur.length - 1].e});
    cur = [];
  };
  for (const w of WORDS) {
    const len = cur.reduce((a, x) => a + x.t.length + 1, 0) + w.t.length;
    if (cur.length >= 3 || (cur.length && len > 20)) flush();
    cur.push(w);
    if (/[,.?!]$/.test(w.t)) flush();
  }
  flush();
  return pages;
})();

export const SENTENCES = [
  'Siz Shahzodani taniysiz, lekin uning haqiqiy ismini bilasizmi?',
  'Oʻzbekistonning eng mashhur estrada yulduzlaridan biri Shahzodaning asl ismi Zilola Musayeva.',
  'U yakkaxon ijodini boshlashdan oldin «Jonim» guruhida qoʻshiq kuylagan,',
  'keyinchalik Shahzoda taxallusi bilan sahnaga chiqib, katta mashhurlikka erishgan.',
  'Uning qoʻshiqlari Oʻzbekistondan tashqarida ham tinglovchilar topgan.',
  'Eng qizigʻi, millionlab odamlar uni tugʻilgandagi ismi bilan emas, sahnadagi taxallusi bilan taniydi.',
  'Sizningcha, Shahzodaning eng zoʻr qoʻshigʻi qaysi?',
];
