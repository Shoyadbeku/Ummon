import { createHash } from "node:crypto";

/** Savol matnini takrorlarni solishtirish uchun normallashtiradi */
export function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFKC")
    .replace(/[ʻʼ‘’`']/g, "'")
    .replace(/[“”«»"]/g, "")
    .replace(/[^\p{L}\p{N}' ]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function textHash(text: string): string {
  return createHash("sha256").update(normalizeText(text)).digest("hex").slice(0, 32);
}

export function wordSet(text: string) {
  return new Set(normalizeText(text).split(" ").filter((w) => w.length > 2));
}

/** So'zlar to'plami bo'yicha Jaccard o'xshashligi (0..1) */
export function similarity(a: string, b: string): number {
  return setSimilarity(wordSet(a), wordSet(b));
}

export function setSimilarity(A: Set<string>, B: Set<string>): number {
  if (!A.size && !B.size) return 1;
  let inter = 0;
  for (const w of A) if (B.has(w)) inter++;
  return inter / (A.size + B.size - inter);
}

export const DUPLICATE_THRESHOLD = 0.85;
