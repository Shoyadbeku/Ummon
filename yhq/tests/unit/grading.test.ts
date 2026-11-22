import { describe, expect, it } from "vitest";
import { grade, nextProgress, isMastered } from "@/lib/grading";

const qs = ["q1", "q2", "q3", "q4"];

describe("grade — natijani hisoblash", () => {
  it("to'g'ri, noto'g'ri va javobsizlarni to'g'ri sanaydi", () => {
    const r = grade(qs, [
      { questionId: "q1", optionId: "a", correctOptionId: "a" },
      { questionId: "q2", optionId: "b", correctOptionId: "a" },
      { questionId: "q3", optionId: null, correctOptionId: "a", revealed: true },
    ], 1);
    expect(r).toMatchObject({ total: 4, correct: 1, wrong: 3, unanswered: 2, percent: 25, passed: false });
    expect(r.perQuestion).toEqual({ q1: true, q2: false, q3: false, q4: false });
  });

  it("ruxsat etilgan xatolar chegarasida o'tgan hisoblanadi", () => {
    const ans = qs.map((q, i) => ({ questionId: q, optionId: i === 0 ? "x" : "a", correctOptionId: "a" }));
    expect(grade(qs, ans, 1).passed).toBe(true);
    expect(grade(qs, ans, 0).passed).toBe(false);
  });

  it("bo'sh test 0%", () => expect(grade([], [], null).percent).toBe(0));

  it("boshqa testga tegishli javoblar hisobga olinmaydi", () => {
    const r = grade(["q1"], [{ questionId: "zzz", optionId: "a", correctOptionId: "a" }], null);
    expect(r.correct).toBe(0);
  });
});

describe("nextProgress — xatolar ro'yxati qoidasi", () => {
  it("xato javob savolni xatolarga qo'shadi", () => {
    const p = nextProgress(null, false);
    expect(p).toMatchObject({ seenCount: 1, wrongCount: 1, inMistakes: true, streak: 0 });
  });
  it("ketma-ket 2 marta to'g'ri ishlanganda xatolardan chiqadi", () => {
    let p = nextProgress(null, false);
    p = nextProgress(p, true);
    expect(p.inMistakes).toBe(true);
    p = nextProgress(p, true);
    expect(p.inMistakes).toBe(false);
    expect(isMastered(p)).toBe(true);
  });
  it("birinchi urinishda to'g'ri — xatolarga tushmaydi", () => {
    expect(nextProgress(null, true).inMistakes).toBe(false);
  });
  it("yana xato qilinsa seriya nolga tushadi", () => {
    let p = nextProgress(null, false);
    p = nextProgress(p, true);
    p = nextProgress(p, false);
    expect(p).toMatchObject({ streak: 0, inMistakes: true, wrongCount: 2, correctCount: 1 });
  });
});
