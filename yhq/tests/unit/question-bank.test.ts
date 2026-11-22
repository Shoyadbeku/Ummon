import { describe, expect, it } from "vitest";
import { QUESTIONS_1 } from "../../prisma/data/questions-1";
import { QUESTIONS_2 } from "../../prisma/data/questions-2";
import { QUESTIONS_3 } from "../../prisma/data/questions-3";
import { SIGNS } from "../../prisma/data/signs";
import { CATEGORIES } from "../../prisma/seed-categories";
import { textHash } from "@/lib/normalize";
import { hasSignArt } from "@/components/sign-icon";

const ALL = [...QUESTIONS_1, ...QUESTIONS_2, ...QUESTIONS_3];
const catSlugs = new Set(CATEGORIES.map((c) => c.slug));
const signCodes = new Set(SIGNS.map((s) => s.code));

describe("savollar bazasi yaxlitligi", () => {
  it("kamida 200 ta savol", () => expect(ALL.length).toBeGreaterThanOrEqual(200));

  it.each(ALL.map((q, i) => [i + 1, q] as const))("%i-savol to'g'ri tuzilgan", (_i, q) => {
    expect(catSlugs.has(q.c)).toBe(true);
    expect(q.o.length).toBeGreaterThanOrEqual(2);
    expect(q.a).toBeGreaterThanOrEqual(0);
    expect(q.a).toBeLessThan(q.o.length);
    expect(new Set(q.o.map((o) => o.toLowerCase())).size).toBe(q.o.length);
    expect(q.e.length).toBeGreaterThan(20);
    expect(q.r).toMatch(/^(\d+|1-ilova.*)$/);
    if (q.sign) expect(signCodes.has(q.sign) || hasSignArt(q.sign)).toBe(true);
    if (q.scene) for (const v of q.scene.vehicles) expect(v.from).not.toBe(v.to);
  });

  it("takroriy savollar yo'q", () => {
    const hashes = ALL.map((q) => textHash(q.q + " " + q.o.join(" ")));
    expect(new Set(hashes).size).toBe(hashes.length);
  });

  it("barcha yo'l belgilari uchun SVG tasvir bor", () => {
    for (const s of SIGNS) expect(hasSignArt(s.code), s.code).toBe(true);
  });
});
