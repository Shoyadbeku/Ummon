import "server-only";
import Papa from "papaparse";
import ExcelJS from "exceljs";
import { questionInputSchema, type QuestionInput } from "../validation";
import { setSimilarity, wordSet, DUPLICATE_THRESHOLD } from "../normalize";
import { prisma } from "../db";
import { hashFor } from "./questions";

/**
 * Import formati (CSV / XLSX ustunlari yoki JSON obyekt maydonlari):
 *   code?, text, option_a, option_b, option_c?, option_d?, option_e?, correct (A–E),
 *   explanation, category (slug), difficulty? (EASY|MEDIUM|HARD), rule_ref?, rule_url?,
 *   origin? (OFFICIAL|PRACTICE), source_id?, image_url?, sign_code?, verification? (UNVERIFIED|IN_REVIEW|VERIFIED)
 * JSON uchun "options": [{ text, isCorrect, explanation? }] ko'rinishi ham qabul qilinadi.
 */
export type RawRow = Record<string, unknown>;
export type ImportRowResult = {
  row: number;
  status: "ok" | "invalid" | "duplicate";
  errors: string[];
  duplicateOf?: string;
  input?: QuestionInput;
  preview: string;
};

const LETTERS = ["a", "b", "c", "d", "e", "f"];

function str(v: unknown) {
  if (v == null) return "";
  if (typeof v === "object" && v && "text" in (v as object)) return String((v as { text: unknown }).text ?? "");
  if (typeof v === "object" && v && "richText" in (v as object)) return ((v as { richText: { text: string }[] }).richText ?? []).map((r) => r.text).join("");
  return String(v).trim();
}

export function rowToInput(raw: RawRow): unknown {
  const r: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(raw)) r[k.trim().toLowerCase().replace(/\s+/g, "_")] = v;
  let options: { text: string; isCorrect: boolean; explanation?: string | null }[];
  if (Array.isArray(r.options)) {
    options = (r.options as Record<string, unknown>[]).map((o) => ({ text: str(o.text), isCorrect: !!(o.isCorrect ?? o.is_correct), explanation: str(o.explanation) || null }));
  } else {
    const correct = str(r.correct).toLowerCase();
    const correctIdx = LETTERS.indexOf(correct) >= 0 ? LETTERS.indexOf(correct) : Number(correct) - 1;
    options = LETTERS.map((l, i) => ({ text: str(r[`option_${l}`]), isCorrect: i === correctIdx, explanation: str(r[`option_${l}_note`]) || null })).filter((o) => o.text);
  }
  const up = (v: unknown, d: string) => (str(v) ? str(v).toUpperCase() : d);
  return {
    code: str(r.code) || undefined,
    text: str(r.text ?? r.question),
    explanation: str(r.explanation),
    imageUrl: str(r.image_url ?? r.imageurl) || null,
    signCode: str(r.sign_code ?? r.signcode) || null,
    categorySlug: str(r.category ?? r.category_slug ?? r.categoryslug),
    difficulty: up(r.difficulty, "MEDIUM"),
    sourceId: str(r.source_id ?? r.sourceid) || null,
    ruleRef: str(r.rule_ref ?? r.ruleref) || null,
    ruleUrl: str(r.rule_url ?? r.ruleurl) || null,
    origin: up(r.origin, "PRACTICE"),
    verificationStatus: up(r.verification ?? r.verification_status, "UNVERIFIED"),
    isActive: true,
    options,
  };
}

export async function parseFile(name: string, buf: Buffer): Promise<RawRow[]> {
  const lower = name.toLowerCase();
  if (lower.endsWith(".json")) {
    const data = JSON.parse(buf.toString("utf8"));
    const arr = Array.isArray(data) ? data : Array.isArray(data.questions) ? data.questions : null;
    if (!arr) throw new Error("JSON massiv yoki { questions: [...] } bo'lishi kerak");
    return arr;
  }
  if (lower.endsWith(".csv")) {
    const res = Papa.parse<RawRow>(buf.toString("utf8").replace(/^﻿/, ""), { header: true, skipEmptyLines: true });
    if (res.errors.length) throw new Error(`CSV xatosi: ${res.errors[0].message} (qator ${res.errors[0].row})`);
    return res.data;
  }
  if (lower.endsWith(".xlsx")) {
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.load(buf as unknown as ArrayBuffer);
    const ws = wb.worksheets[0];
    if (!ws) throw new Error("Excel faylda varaq yo'q");
    const headers: string[] = [];
    ws.getRow(1).eachCell({ includeEmpty: true }, (cell, col) => (headers[col] = str(cell.value)));
    const rows: RawRow[] = [];
    ws.eachRow((row, idx) => {
      if (idx === 1) return;
      const obj: RawRow = {};
      row.eachCell({ includeEmpty: true }, (cell, col) => { if (headers[col]) obj[headers[col]] = cell.value; });
      if (Object.values(obj).some((v) => str(v))) rows.push(obj);
    });
    return rows;
  }
  throw new Error("Faqat .csv, .json yoki .xlsx fayllar qabul qilinadi");
}

/** Validatsiya va takrorlarni aniqlash (fayl ichida ham, bazaga nisbatan ham) */
export async function analyzeRows(rows: RawRow[]): Promise<ImportRowResult[]> {
  const [cats, existing] = await Promise.all([
    prisma.category.findMany({ select: { slug: true } }),
    prisma.question.findMany({ select: { code: true, text: true, textHash: true } }),
  ]);
  const catSet = new Set(cats.map((c) => c.slug));
  const hashMap = new Map(existing.map((q) => [q.textHash, q.code]));
  const codeSet = new Set(existing.map((q) => q.code));
  const seenInFile = new Map<string, number>();
  const accepted: { words: Set<string>; row: number }[] = [];
  const existingWords = existing.map((q) => ({ code: q.code, words: wordSet(q.text) }));

  return rows.map((raw, i) => {
    const row = i + 2; // sarlavha qatori 1
    const parsed = questionInputSchema.safeParse(rowToInput(raw));
    const preview = str((raw as RawRow).text ?? (raw as RawRow).question).slice(0, 120);
    if (!parsed.success) {
      return { row, status: "invalid", errors: parsed.error.issues.map((e) => `${e.path.join(".") || "qator"}: ${e.message}`), preview };
    }
    const input = parsed.data;
    const errors: string[] = [];
    if (!catSet.has(input.categorySlug)) errors.push(`categorySlug: noma'lum mavzu "${input.categorySlug}"`);
    if (input.code && codeSet.has(input.code)) errors.push(`code: "${input.code}" bazada yoki faylda takrorlangan`);
    if (errors.length) return { row, status: "invalid", errors, preview, input };
    const h = hashFor(input);
    if (hashMap.has(h)) return { row, status: "duplicate", errors: [], duplicateOf: hashMap.get(h), preview, input };
    if (seenInFile.has(h)) return { row, status: "duplicate", errors: [], duplicateOf: `fayldagi ${seenInFile.get(h)}-qator`, preview, input };
    const words = wordSet(input.text);
    const similar = existingWords.find((q) => setSimilarity(q.words, words) >= DUPLICATE_THRESHOLD) ?? null;
    if (similar) return { row, status: "duplicate", errors: [], duplicateOf: `${similar.code} (o'xshash)`, preview, input };
    const similarInFile = accepted.find((a) => setSimilarity(a.words, words) >= DUPLICATE_THRESHOLD);
    if (similarInFile) return { row, status: "duplicate", errors: [], duplicateOf: `fayldagi ${similarInFile.row}-qator (o'xshash)`, preview, input };
    seenInFile.set(h, row);
    if (input.code) codeSet.add(input.code);
    accepted.push({ words, row });
    return { row, status: "ok", errors: [], preview, input };
  });
}
