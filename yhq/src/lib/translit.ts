// O'zbek lotin → kirill transliteratsiyasi (interfeys va savollarni kirillda ko'rsatish uchun)
const APOS = "['‘’ʻʼ`]";
const RULES: [RegExp, string][] = [
  [new RegExp("o" + APOS, "g"), "ў"], [new RegExp("O" + APOS, "g"), "Ў"],
  [new RegExp("g" + APOS, "g"), "ғ"], [new RegExp("G" + APOS, "g"), "Ғ"],
  [/sh/g, "ш"], [/S[hH]/g, "Ш"], [/ch/g, "ч"], [/C[hH]/g, "Ч"],
  [/yo/g, "ё"], [/Y[oO]/g, "Ё"], [/yu/g, "ю"], [/Y[uU]/g, "Ю"], [/ya/g, "я"], [/Y[aA]/g, "Я"],
  [/ye/g, "е"], [/Y[eE]/g, "Е"],
  [/(?<![\p{L}\p{N}])e/gu, "э"], [/(?<![\p{L}\p{N}])E/gu, "Э"],
  [new RegExp(APOS, "g"), "ъ"],
];
const SINGLE: Record<string, string> = {
  a: "а", b: "б", v: "в", g: "г", d: "д", e: "е", j: "ж", z: "з", i: "и", y: "й", k: "к", l: "л",
  m: "м", n: "н", o: "о", p: "п", r: "р", s: "с", t: "т", u: "у", f: "ф", x: "х", q: "қ", h: "ҳ", c: "с", w: "в",
};

// URL, raqamli belgi kodlari (2.1, 3.24) va lotin qisqartmalar (YHQ, DYHXX) o'zgarmasligi uchun
const KEEP = /(https?:\/\/\S+|\b[A-Z]{2,}\b|“[A-Z0-9]+”|"[A-Z0-9]+")/g;

function convert(chunk: string) {
  let s = chunk;
  for (const [re, rep] of RULES) s = s.replace(re, rep);
  let out = "";
  for (const ch of s) {
    const low = ch.toLowerCase();
    if (low in SINGLE) {
      const r = SINGLE[low];
      out += ch === low ? r : r.toUpperCase();
    } else out += ch;
  }
  return out;
}

export function toCyrillic(text: string): string {
  if (!text) return text;
  const parts = text.split(KEEP);
  return parts.map((p, i) => (i % 2 === 1 ? p : convert(p))).join("");
}
