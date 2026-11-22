export type GradableAnswer = { questionId: string; optionId: string | null; correctOptionId: string; revealed?: boolean };

export type GradeResult = {
  total: number;
  correct: number;
  wrong: number;
  unanswered: number;
  percent: number;
  passed: boolean;
  perQuestion: Record<string, boolean>;
};

/**
 * Natijani hisoblash. Javob berilmagan yoki o'quv rejimida javobi oldindan ko'rilgan
 * (va keyin tanlanmagan) savol noto'g'ri hisoblanadi.
 */
export function grade(questionIds: string[], answers: GradableAnswer[], maxErrors: number | null): GradeResult {
  const byQ = new Map(answers.map((a) => [a.questionId, a]));
  let correct = 0;
  let unanswered = 0;
  const perQuestion: Record<string, boolean> = {};
  for (const qid of questionIds) {
    const a = byQ.get(qid);
    const ok = !!a && a.optionId != null && a.optionId === a.correctOptionId;
    if (!a || a.optionId == null) unanswered++;
    if (ok) correct++;
    perQuestion[qid] = ok;
  }
  const total = questionIds.length;
  const wrong = total - correct;
  const allowed = maxErrors ?? 0;
  return {
    total,
    correct,
    wrong,
    unanswered,
    percent: total ? Math.round((correct / total) * 100) : 0,
    passed: wrong <= allowed,
    perQuestion,
  };
}

/** Savol bo'yicha o'zlashtirish holatini yangilash qoidasi */
export function nextProgress(
  prev: { seenCount: number; correctCount: number; wrongCount: number; streak: number; inMistakes: boolean } | null,
  isCorrect: boolean,
) {
  const p = prev ?? { seenCount: 0, correctCount: 0, wrongCount: 0, streak: 0, inMistakes: false };
  const streak = isCorrect ? p.streak + 1 : 0;
  return {
    seenCount: p.seenCount + 1,
    correctCount: p.correctCount + (isCorrect ? 1 : 0),
    wrongCount: p.wrongCount + (isCorrect ? 0 : 1),
    streak,
    lastCorrect: isCorrect,
    // Xato qilingan savol "xatolar" ro'yxatiga tushadi; ketma-ket 2 marta to'g'ri ishlanganda chiqariladi
    inMistakes: isCorrect ? (p.inMistakes ? streak < 2 : false) : true,
  };
}

/** O'zlashtirilgan: kamida 1 marta ko'rilgan, oxirgi javob to'g'ri va xatolar ro'yxatida emas */
export function isMastered(p: { lastCorrect: boolean | null; inMistakes: boolean }) {
  return p.lastCorrect === true && !p.inMistakes;
}
