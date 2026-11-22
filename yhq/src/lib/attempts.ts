import "server-only";
import { cookies } from "next/headers";
import { randomUUID } from "node:crypto";
import type { AttemptKind, AttemptMode, Prisma } from "@prisma/client";
import { prisma } from "./db";
import { getActor, actorWhere, type Actor } from "./actor";
import { HttpError } from "./auth";
import { getSettings, visibleQuestionWhere } from "./settings";
import { grade, nextProgress } from "./grading";
import { shuffle } from "./utils";
import { GUEST_COOKIE } from "./session-constants";
import { QUESTIONS_PER_TICKET } from "./tickets";

/** Route handler ichida: aktor yo'q bo'lsa mehmon cookie yaratadi */
export async function ensureActor(): Promise<Actor> {
  const actor = await getActor();
  if (actor.user || actor.guestId) return actor;
  const gid = randomUUID();
  const jar = await cookies();
  jar.set(GUEST_COOKIE, gid, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production" && !process.env.INSECURE_COOKIES,
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
  });
  return { user: null, guestId: gid };
}

function ownerData(actor: Actor) {
  return actor.user ? { userId: actor.user.id } : { guestId: actor.guestId! };
}

export type StartInput = {
  kind: AttemptKind;
  mode: AttemptMode;
  ticketNumber?: number;
  categorySlug?: string;
  count?: number;
  signsOnly?: boolean;
};

export async function startAttempt(input: StartInput) {
  const actor = await ensureActor();
  const settings = await getSettings();
  const visible = visibleQuestionWhere(settings);
  let questionIds: string[] = [];
  let ticketId: string | null = null;
  let mode = input.mode;
  let deadlineAt: Date | null = null;
  let maxErrors: number | null = null;
  const count = Math.min(Math.max(input.count ?? QUESTIONS_PER_TICKET, 5), 50);

  switch (input.kind) {
    case "TICKET": {
      if (!input.ticketNumber) throw new HttpError(400, "Bilet raqami ko'rsatilmagan");
      const ticket = await prisma.ticket.findUnique({
        where: { number: input.ticketNumber },
        include: { questions: { orderBy: { position: "asc" }, include: { question: { select: { id: true, isActive: true, verificationStatus: true } } } } },
      });
      if (!ticket || !ticket.isPublished) throw new HttpError(404, "Bilet topilmadi");
      questionIds = ticket.questions
        .filter((tq) => tq.question.isActive && tq.question.verificationStatus !== "REJECTED")
        .map((tq) => tq.questionId);
      ticketId = ticket.id;
      if (mode === "EXAM") {
        // Bilet imtihon rejimida: vaqt umumiy imtihon vaqtiga proporsional
        const minutes = Math.max(1, Math.ceil((settings.examTimeMinutes * questionIds.length) / settings.examQuestionCount));
        deadlineAt = new Date(Date.now() + minutes * 60_000);
        maxErrors = Math.floor((settings.examMaxErrors * questionIds.length) / settings.examQuestionCount);
      }
      break;
    }
    case "EXAM": {
      mode = "EXAM";
      const ids = await prisma.question.findMany({ where: visible, select: { id: true } });
      questionIds = shuffle(ids.map((q) => q.id)).slice(0, settings.examQuestionCount);
      deadlineAt = new Date(Date.now() + settings.examTimeMinutes * 60_000);
      maxErrors = settings.examMaxErrors;
      break;
    }
    case "RANDOM": {
      const ids = await prisma.question.findMany({ where: visible, select: { id: true } });
      questionIds = shuffle(ids.map((q) => q.id)).slice(0, count);
      break;
    }
    case "TOPIC":
    case "SIGNS": {
      const slug = input.kind === "SIGNS" ? "belgilar" : input.categorySlug;
      if (!slug) throw new HttpError(400, "Mavzu ko'rsatilmagan");
      const where: Prisma.QuestionWhereInput =
        input.kind === "SIGNS"
          ? { ...visible, OR: [{ category: { slug } }, { signCode: { not: null } }] }
          : { ...visible, category: { slug } };
      const ids = await prisma.question.findMany({ where, select: { id: true } });
      questionIds = shuffle(ids.map((q) => q.id)).slice(0, count);
      break;
    }
    case "MISTAKES": {
      const w = actorWhere(actor);
      const rows = w
        ? await prisma.userProgress.findMany({ where: { ...w, inMistakes: true, question: visible }, select: { questionId: true } })
        : [];
      questionIds = shuffle(rows.map((r) => r.questionId)).slice(0, count);
      break;
    }
    case "FAVORITES": {
      const w = actorWhere(actor);
      const rows = w ? await prisma.savedQuestion.findMany({ where: { ...w, question: visible }, select: { questionId: true } }) : [];
      questionIds = shuffle(rows.map((r) => r.questionId)).slice(0, count);
      break;
    }
  }

  if (!questionIds.length) throw new HttpError(404, "Bu bo'lim uchun savollar topilmadi");

  // Shu bilet bo'yicha tugallanmagan urinishlar eskirgan deb belgilanadi
  if (ticketId) {
    await prisma.testAttempt.updateMany({
      where: { ...ownerData(actor), ticketId, status: "IN_PROGRESS" },
      data: { status: "EXPIRED", finishedAt: new Date() },
    });
  }

  const attempt = await prisma.testAttempt.create({
    data: {
      ...ownerData(actor),
      mode,
      kind: input.kind,
      ticketId,
      categorySlug: input.kind === "TOPIC" ? input.categorySlug : null,
      questionIds,
      total: questionIds.length,
      deadlineAt,
      maxErrors,
    },
  });
  return attempt;
}

export async function loadOwnedAttempt(id: string, actor?: Actor) {
  const a = actor ?? (await getActor());
  const attempt = await prisma.testAttempt.findUnique({ where: { id }, include: { answers: true, ticket: { select: { number: true } } } });
  if (!attempt) throw new HttpError(404, "Test topilmadi");
  const owns = (a.user && attempt.userId === a.user.id) || (!a.user && a.guestId && attempt.guestId === a.guestId);
  if (!owns) throw new HttpError(404, "Test topilmadi");
  return { attempt, actor: a };
}

const questionSelect = {
  id: true,
  code: true,
  text: true,
  imageUrl: true,
  scene: true,
  signCode: true,
  origin: true,
  verificationStatus: true,
  ruleRef: true,
  ruleUrl: true,
  explanation: true,
  translations: true,
  category: { select: { slug: true, name: true } },
  source: { select: { name: true, url: true, type: true } },
  options: { orderBy: { order: "asc" as const }, select: { id: true, order: true, text: true, isCorrect: true, explanation: true } },
} satisfies Prisma.QuestionSelect;

type FullQuestion = Prisma.QuestionGetPayload<{ select: typeof questionSelect }>;

export type Feedback = {
  questionId: string;
  isCorrect: boolean;
  selectedOptionId: string | null;
  correctOptionId: string;
  explanation: string;
  ruleRef: string | null;
  ruleUrl: string | null;
  sourceName: string | null;
  sourceUrl: string | null;
  options: { id: string; text: string; isCorrect: boolean; explanation: string | null }[];
};

function toFeedback(q: FullQuestion, selectedOptionId: string | null): Feedback {
  const correct = q.options.find((o) => o.isCorrect);
  return {
    questionId: q.id,
    isCorrect: !!correct && selectedOptionId === correct.id,
    selectedOptionId,
    correctOptionId: correct?.id ?? "",
    explanation: q.explanation,
    ruleRef: q.ruleRef,
    ruleUrl: q.ruleUrl,
    sourceName: q.source?.name ?? null,
    sourceUrl: q.source?.url ?? null,
    options: q.options.map((o) => ({ id: o.id, text: o.text, isCorrect: o.isCorrect, explanation: o.explanation })),
  };
}

function isExpired(a: { deadlineAt: Date | null }) {
  return !!a.deadlineAt && a.deadlineAt.getTime() + 5_000 < Date.now(); // 5 soniya tarmoq kechikishi uchun
}

/** Mijozga yuboriladigan holat. Imtihon rejimida to'g'ri javoblar faqat test yakunlangandan so'ng beriladi. */
export async function getAttemptView(id: string) {
  const { attempt, actor } = await loadOwnedAttempt(id);
  if (attempt.status === "IN_PROGRESS" && isExpired(attempt)) {
    await finishAttempt(id);
    return getAttemptView(id);
  }
  const questions = await prisma.question.findMany({ where: { id: { in: attempt.questionIds } }, select: questionSelect });
  const byId = new Map(questions.map((q) => [q.id, q]));
  const ordered = attempt.questionIds.map((qid) => byId.get(qid)).filter(Boolean) as FullQuestion[];
  const answers = new Map(attempt.answers.map((a) => [a.questionId, a]));
  const finished = attempt.status !== "IN_PROGRESS";
  const w = actorWhere(actor);
  const saved = w
    ? new Set((await prisma.savedQuestion.findMany({ where: { ...w, questionId: { in: attempt.questionIds } }, select: { questionId: true } })).map((s) => s.questionId))
    : new Set<string>();

  return {
    id: attempt.id,
    mode: attempt.mode,
    kind: attempt.kind,
    status: attempt.status,
    ticketNumber: attempt.ticket?.number ?? null,
    categorySlug: attempt.categorySlug,
    startedAt: attempt.startedAt.toISOString(),
    deadlineAt: attempt.deadlineAt?.toISOString() ?? null,
    serverNow: new Date().toISOString(),
    total: attempt.total,
    maxErrors: attempt.maxErrors,
    questions: ordered.map((q) => {
      const ans = answers.get(q.id);
      const showAnswer = finished || (attempt.mode === "LEARN" && !!ans && (ans.checked || ans.revealed));
      return {
        id: q.id,
        code: q.code,
        text: q.text,
        imageUrl: q.imageUrl,
        scene: q.scene,
        signCode: q.signCode,
        origin: q.origin,
        verificationStatus: q.verificationStatus,
        category: q.category,
        translations: q.translations,
        saved: saved.has(q.id),
        options: q.options.map((o) => ({ id: o.id, text: o.text })),
        answer: ans ? { optionId: ans.optionId, checked: ans.checked, revealed: ans.revealed } : null,
        feedback: showAnswer ? toFeedback(q, ans?.optionId ?? null) : null,
      };
    }),
  };
}

export type AttemptView = Awaited<ReturnType<typeof getAttemptView>>;

async function updateProgress(actor: Actor, questionId: string, isCorrect: boolean) {
  const w = actor.user ? { userId: actor.user.id } : actor.guestId ? { guestId: actor.guestId } : null;
  if (!w) return;
  const where = actor.user
    ? { userId_questionId: { userId: actor.user.id, questionId } }
    : { guestId_questionId: { guestId: actor.guestId!, questionId } };
  const prev = await prisma.userProgress.findUnique({ where });
  const next = nextProgress(prev, isCorrect);
  await prisma.userProgress.upsert({
    where,
    create: { ...w, questionId, ...next, lastAnsweredAt: new Date() },
    update: { ...next, lastAnsweredAt: new Date() },
  });
}

/**
 * Javobni qayd etish.
 * - O'quv rejimi: javob tekshiriladi va izoh bilan qaytariladi (bir marta tekshirilgan javob o'zgarmaydi).
 * - Imtihon rejimi: javob saqlanadi, to'g'riligi aytilmaydi, test yakunlanguncha o'zgartirish mumkin.
 */
export async function submitAnswer(attemptId: string, questionId: string, optionId: string) {
  const { attempt, actor } = await loadOwnedAttempt(attemptId);
  if (attempt.status !== "IN_PROGRESS") throw new HttpError(409, "Test allaqachon yakunlangan");
  if (isExpired(attempt)) {
    await finishAttempt(attemptId);
    throw new HttpError(409, "Vaqt tugadi, test yakunlandi");
  }
  if (!attempt.questionIds.includes(questionId)) throw new HttpError(400, "Savol bu testga tegishli emas");
  const q = await prisma.question.findUnique({ where: { id: questionId }, select: questionSelect });
  if (!q) throw new HttpError(404, "Savol topilmadi");
  const opt = q.options.find((o) => o.id === optionId);
  if (!opt) throw new HttpError(400, "Javob varianti noto'g'ri");

  const existing = attempt.answers.find((a) => a.questionId === questionId);
  if (attempt.mode === "LEARN" && existing && (existing.checked || existing.revealed)) {
    return { saved: false, feedback: toFeedback(q, existing.optionId) };
  }

  await prisma.userAnswer.upsert({
    where: { attemptId_questionId: { attemptId, questionId } },
    create: { attemptId, questionId, optionId, isCorrect: opt.isCorrect, checked: attempt.mode === "LEARN" },
    update: { optionId, isCorrect: opt.isCorrect, checked: attempt.mode === "LEARN", answeredAt: new Date() },
  });

  if (attempt.mode === "LEARN") {
    await updateProgress(actor, questionId, opt.isCorrect);
    return { saved: true, feedback: toFeedback(q, optionId) };
  }
  return { saved: true, feedback: null };
}

/** O'quv rejimida to'g'ri javobni oldindan ko'rish (imtihon rejimida taqiqlangan) */
export async function revealAnswer(attemptId: string, questionId: string) {
  const { attempt, actor } = await loadOwnedAttempt(attemptId);
  if (attempt.mode !== "LEARN" && attempt.status === "IN_PROGRESS") {
    throw new HttpError(403, "Imtihon rejimida javoblar test yakunlangandan keyin ko'rsatiladi");
  }
  if (!attempt.questionIds.includes(questionId)) throw new HttpError(400, "Savol bu testga tegishli emas");
  const q = await prisma.question.findUnique({ where: { id: questionId }, select: questionSelect });
  if (!q) throw new HttpError(404, "Savol topilmadi");
  const existing = attempt.answers.find((a) => a.questionId === questionId);
  if (attempt.status === "IN_PROGRESS" && !existing?.checked) {
    // Javobsiz oldindan ko'rilgan savol xato hisoblanadi va "xatolar"ga qo'shiladi
    await prisma.userAnswer.upsert({
      where: { attemptId_questionId: { attemptId, questionId } },
      create: { attemptId, questionId, optionId: null, isCorrect: false, revealed: true },
      update: { revealed: true },
    });
    if (!existing) await updateProgress(actor, questionId, false);
  }
  return toFeedback(q, existing?.optionId ?? null);
}

export async function finishAttempt(attemptId: string) {
  const { attempt, actor } = await loadOwnedAttempt(attemptId);
  if (attempt.status !== "IN_PROGRESS") return attempt;
  const questions = await prisma.question.findMany({
    where: { id: { in: attempt.questionIds } },
    select: { id: true, options: { where: { isCorrect: true }, select: { id: true } } },
  });
  const correctMap = new Map(questions.map((q) => [q.id, q.options[0]?.id ?? ""]));
  const result = grade(
    attempt.questionIds,
    attempt.answers.map((a) => ({ questionId: a.questionId, optionId: a.optionId, correctOptionId: correctMap.get(a.questionId) ?? "" })),
    attempt.maxErrors,
  );

  // Imtihon rejimida progress faqat yakunda yangilanadi (o'quv rejimida — har bir tekshiruvda)
  if (attempt.mode === "EXAM") {
    const answered = new Set(attempt.answers.map((a) => a.questionId));
    for (const qid of attempt.questionIds) {
      await updateProgress(actor, qid, answered.has(qid) && result.perQuestion[qid]);
    }
  }

  const now = new Date();
  const expired = isExpired(attempt);
  const end = expired && attempt.deadlineAt ? attempt.deadlineAt : now;
  return prisma.testAttempt.update({
    where: { id: attemptId },
    data: {
      status: "FINISHED",
      finishedAt: end,
      correctCount: result.correct,
      wrongCount: result.wrong,
      durationSec: Math.max(0, Math.round((end.getTime() - attempt.startedAt.getTime()) / 1000)),
      passed: attempt.maxErrors != null ? result.passed : result.wrong === 0,
    },
  });
}

/** Natija sahifasi uchun: avvalgi urinishlar bilan taqqoslash */
export async function getResultSummary(attemptId: string) {
  const { attempt, actor } = await loadOwnedAttempt(attemptId);
  if (attempt.status === "IN_PROGRESS") throw new HttpError(409, "Test hali yakunlanmagan");
  const w = actorWhere(actor)!;
  const previous = await prisma.testAttempt.findMany({
    where: {
      ...w,
      status: "FINISHED",
      id: { not: attempt.id },
      startedAt: { lt: attempt.startedAt },
      ...(attempt.ticketId ? { ticketId: attempt.ticketId } : { kind: attempt.kind }),
    },
    orderBy: { startedAt: "desc" },
    take: 5,
    select: { id: true, correctCount: true, total: true, finishedAt: true, durationSec: true },
  });
  let nextTicket: number | null = null;
  if (attempt.ticket) {
    const n = await prisma.ticket.findFirst({
      where: { number: { gt: attempt.ticket.number }, isPublished: true },
      orderBy: { number: "asc" },
      select: { number: true },
    });
    nextTicket = n?.number ?? null;
  }
  return { attempt, previous, nextTicket };
}
