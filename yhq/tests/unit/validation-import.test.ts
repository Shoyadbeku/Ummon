import { describe, expect, it } from "vitest";
import { questionInputSchema } from "@/lib/validation";
import { rowToInput } from "@/lib/admin/import";

const base = {
  text: "Aholi punktidan tashqarida tezlik qancha?",
  explanation: "79-bandga ko'ra 100 km/soat.",
  categorySlug: "tezlik",
  options: [
    { text: "90", isCorrect: false },
    { text: "100", isCorrect: true },
  ],
};

describe("questionInputSchema — savol validatsiyasi", () => {
  it("to'g'ri savolni qabul qiladi", () => {
    expect(questionInputSchema.safeParse(base).success).toBe(true);
  });
  it("to'g'ri javob bitta bo'lishi shart", () => {
    const r = questionInputSchema.safeParse({ ...base, options: base.options.map((o) => ({ ...o, isCorrect: true })) });
    expect(r.success).toBe(false);
    const none = questionInputSchema.safeParse({ ...base, options: base.options.map((o) => ({ ...o, isCorrect: false })) });
    expect(none.success).toBe(false);
  });
  it("takroriy variantlarni rad etadi", () => {
    expect(questionInputSchema.safeParse({ ...base, options: [{ text: "A", isCorrect: true }, { text: "a", isCorrect: false }] }).success).toBe(false);
  });
  it("rasmiy savol manbasiz bo'lmaydi", () => {
    expect(questionInputSchema.safeParse({ ...base, origin: "OFFICIAL" }).success).toBe(false);
    expect(questionInputSchema.safeParse({ ...base, origin: "OFFICIAL", sourceId: "src1" }).success).toBe(true);
  });
  it("kamida 2 ta variant", () => {
    expect(questionInputSchema.safeParse({ ...base, options: [{ text: "x", isCorrect: true }] }).success).toBe(false);
  });
});

describe("import qatorini o'girish", () => {
  it("CSV ustunlarini savolga aylantiradi (correct = harf)", () => {
    const r = questionInputSchema.parse(rowToInput({
      text: "Savol matni bu yerda", option_a: "Bir", option_b: "Ikki", option_c: "Uch", correct: "B",
      explanation: "Izoh matni", category: "tezlik", difficulty: "hard", origin: "",
    }));
    expect(r.options.map((o) => o.isCorrect)).toEqual([false, true, false]);
    expect(r.difficulty).toBe("HARD");
    expect(r.origin).toBe("PRACTICE");
  });
  it("JSON options massivini qabul qiladi", () => {
    const r = questionInputSchema.parse(rowToInput({
      text: "Savol matni bu yerda", explanation: "Izoh matni", category: "tezlik",
      options: [{ text: "x", isCorrect: false }, { text: "y", isCorrect: true }],
    }));
    expect(r.options[1].isCorrect).toBe(true);
  });
  it("to'g'ri javob ko'rsatilmasa validatsiyadan o'tmaydi", () => {
    expect(questionInputSchema.safeParse(rowToInput({ text: "Savol matni", option_a: "x", option_b: "y", explanation: "izoh matni", category: "tezlik" })).success).toBe(false);
  });
});
