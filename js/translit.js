// O‘zbek lotin ⇄ kirill transliteratsiyasi (2024-yilgi lotin imlosi: o‘, g‘, sh, ch).

const CYR_TO_LAT = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ж: 'j', з: 'z', и: 'i', й: 'y', к: 'k', л: 'l',
  м: 'm', н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'x', ц: 's',
  ч: 'ch', ш: 'sh', щ: 'sh', ъ: '’', ь: '', ы: 'i', э: 'e', ю: 'yu', я: 'ya', ё: 'yo',
  ў: 'o‘', қ: 'q', ғ: 'g‘', ҳ: 'h',
};
const VOWELS_CYR = 'аеёиоуўэюяы';

export function hasCyrillic(s) { return /[Ѐ-ӿ]/.test(s); }

export function toLatin(text) {
  let out = '';
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const low = ch.toLowerCase();
    const isUpper = ch !== low;
    let r;
    if (low === 'е') {
      // so‘z boshida yoki unlidan keyin "ye"
      const prev = (text[i - 1] || ' ').toLowerCase();
      r = (!/[Ѐ-ӿa-z]/i.test(prev) || VOWELS_CYR.includes(prev) || prev === 'ъ' || prev === 'ь') ? 'ye' : 'e';
    } else if (low === 'ц') {
      const prev = (text[i - 1] || ' ').toLowerCase();
      r = (!/[Ѐ-ӿ]/.test(prev) || VOWELS_CYR.includes(prev)) ? 'ts' : 's';
    } else if (low in CYR_TO_LAT) {
      r = CYR_TO_LAT[low];
    } else {
      out += ch; continue;
    }
    if (isUpper && r) {
      const nextUpper = text[i + 1] && text[i + 1] !== text[i + 1].toLowerCase();
      r = nextUpper || r.length === 1 ? r.toUpperCase() : r[0].toUpperCase() + r.slice(1);
    }
    out += r;
  }
  return out;
}

const APOS = "['‘’ʻʼ`]";
const LAT_RULES = [
  [new RegExp('o' + APOS, 'g'), 'ў'], [new RegExp('O' + APOS, 'g'), 'Ў'],
  [new RegExp('g' + APOS, 'g'), 'ғ'], [new RegExp('G' + APOS, 'g'), 'Ғ'],
  [/sh/g, 'ш'], [/S[hH]/g, 'Ш'], [/ch/g, 'ч'], [/C[hH]/g, 'Ч'],
  [/yo/g, 'ё'], [/Y[oO]/g, 'Ё'], [/yu/g, 'ю'], [/Y[uU]/g, 'Ю'], [/ya/g, 'я'], [/Y[aA]/g, 'Я'],
  [/ye/g, 'е'], [/Y[eE]/g, 'Е'],
  [/(?<!\p{L})e/gu, 'э'], [/(?<!\p{L})E/gu, 'Э'],
  [new RegExp(APOS, 'g'), 'ъ'],
];
const LAT_SINGLE = {
  a: 'а', b: 'б', v: 'в', g: 'г', d: 'д', e: 'е', j: 'ж', z: 'з', i: 'и', y: 'й', k: 'к', l: 'л',
  m: 'м', n: 'н', o: 'о', p: 'п', r: 'р', s: 'с', t: 'т', u: 'у', f: 'ф', x: 'х', q: 'қ', h: 'ҳ', c: 'с', w: 'в',
};

export function toCyrillic(text) {
  let s = text;
  for (const [re, rep] of LAT_RULES) s = s.replace(re, rep);
  let out = '';
  for (const ch of s) {
    const low = ch.toLowerCase();
    if (low in LAT_SINGLE) {
      const r = LAT_SINGLE[low];
      out += ch === low ? r : r.toUpperCase();
    } else out += ch;
  }
  return out;
}

// Turli apostroflarni bitta ko‘rinishga keltirish (o‘ g‘)
export function normalizeApostrophes(text) {
  return text.replace(/([oOgG])['ʻʼ`’]/g, '$1‘');
}
