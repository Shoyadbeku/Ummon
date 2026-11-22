import "server-only";
import { prisma } from "./db";
import { actorWhere, type Actor } from "./actor";
import { ticketStatus, type TicketStatus } from "./tickets";
import { getSettings, visibleQuestionWhere } from "./settings";

export async function getHomeStats() {
  const settings = await getSettings();
  const [questions, tickets, signs, topics] = await Promise.all([
    prisma.question.count({ where: visibleQuestionWhere(settings) }),
    prisma.ticket.count({ where: { isPublished: true } }),
    prisma.trafficSign.count(),
    prisma.category.count(),
  ]);
  return { questions, tickets, signs, topics };
}

export type TicketRow = {
  number: number;
  title: string | null;
  status: TicketStatus;
  lastCorrect: number | null;
  lastTotal: number | null;
  lastAt: Date | null;
  inProgressId: string | null;
  questionCount: number;
};

export async function getTicketsWithStatus(actor: Actor): Promise<TicketRow[]> {
  const w = actorWhere(actor);
  const tickets = await prisma.ticket.findMany({
    where: { isPublished: true },
    orderBy: { number: "asc" },
    select: { id: true, number: true, title: true, _count: { select: { questions: true } } },
  });
  const attempts = w
    ? await prisma.testAttempt.findMany({
        where: { ...w, ticketId: { not: null }, status: { in: ["IN_PROGRESS", "FINISHED"] } },
        orderBy: { startedAt: "desc" },
        select: { id: true, ticketId: true, status: true, wrongCount: true, correctCount: true, total: true, startedAt: true, finishedAt: true },
      })
    : [];
  const byTicket = new Map<string, typeof attempts>();
  for (const a of attempts) {
    const list = byTicket.get(a.ticketId!) ?? [];
    list.push(a);
    byTicket.set(a.ticketId!, list);
  }
  return tickets.map((t) => {
    const list = byTicket.get(t.id) ?? [];
    const status = ticketStatus(list.map((a) => ({ status: a.status, wrongCount: a.wrongCount, startedAt: a.startedAt })));
    const lastFinished = list.find((a) => a.status === "FINISHED");
    const inProgress = list[0]?.status === "IN_PROGRESS" ? list[0] : null;
    return {
      number: t.number,
      title: t.title,
      status,
      lastCorrect: lastFinished?.correctCount ?? null,
      lastTotal: lastFinished?.total ?? null,
      lastAt: inProgress?.startedAt ?? lastFinished?.finishedAt ?? null,
      inProgressId: inProgress?.id ?? null,
      questionCount: t._count.questions,
    };
  });
}

export async function getMistakes(actor: Actor) {
  const w = actorWhere(actor);
  if (!w) return { mistakes: [], mastered: 0, seen: 0 };
  const [rows, mastered, seen] = await Promise.all([
    prisma.userProgress.findMany({
      where: { ...w, inMistakes: true, question: { isActive: true } },
      orderBy: { lastAnsweredAt: "desc" },
      select: {
        wrongCount: true,
        correctCount: true,
        lastAnsweredAt: true,
        question: {
          select: {
            id: true, code: true, text: true, ruleRef: true, signCode: true, explanation: true,
            category: { select: { name: true } },
            options: { where: { isCorrect: true }, select: { text: true } },
          },
        },
      },
    }),
    prisma.userProgress.count({ where: { ...w, inMistakes: false, lastCorrect: true } }),
    prisma.userProgress.count({ where: w }),
  ]);
  return { mistakes: rows, mastered, seen };
}

export async function getTopics(actor: Actor) {
  const settings = await getSettings();
  const w = actorWhere(actor);
  const cats = await prisma.category.findMany({
    orderBy: { order: "asc" },
    select: { id: true, slug: true, name: true, nameRu: true, description: true, _count: { select: { questions: { where: visibleQuestionWhere(settings) } } } },
  });
  const mastered = w
    ? await prisma.userProgress.findMany({ where: { ...w, lastCorrect: true, inMistakes: false }, select: { question: { select: { categoryId: true } } } })
    : [];
  const mByCat = new Map<string, number>();
  for (const m of mastered) mByCat.set(m.question.categoryId, (mByCat.get(m.question.categoryId) ?? 0) + 1);
  return cats.map((c) => ({ ...c, count: c._count.questions, mastered: mByCat.get(c.id) ?? 0 }));
}

export async function getCabinet(actor: Actor) {
  const w = actorWhere(actor);
  if (!w) return null;
  const [attempts, progressAgg, mistakesCount, saved, ticketsDone] = await Promise.all([
    prisma.testAttempt.findMany({
      where: { ...w, status: { in: ["FINISHED", "IN_PROGRESS"] } },
      orderBy: { startedAt: "desc" },
      take: 60,
      select: { id: true, kind: true, mode: true, status: true, correctCount: true, wrongCount: true, total: true, startedAt: true, finishedAt: true, durationSec: true, ticket: { select: { number: true } } },
    }),
    prisma.userProgress.aggregate({ where: w, _sum: { correctCount: true, wrongCount: true }, _count: true }),
    prisma.userProgress.count({ where: { ...w, inMistakes: true } }),
    prisma.savedQuestion.findMany({
      where: w,
      orderBy: { createdAt: "desc" },
      select: { question: { select: { id: true, code: true, text: true, ruleRef: true, category: { select: { name: true } } } } },
    }),
    prisma.testAttempt.findMany({ where: { ...w, status: "FINISHED", ticketId: { not: null } }, distinct: ["ticketId"], select: { ticketId: true } }),
  ]);
  const finished = attempts.filter((a) => a.status === "FINISHED");
  const correct = progressAgg._sum.correctCount ?? 0;
  const wrong = progressAgg._sum.wrongCount ?? 0;
  // Grafik: oxirgi 20 ta yakunlangan test bo'yicha foiz
  const chart = finished
    .slice(0, 20)
    .reverse()
    .map((a, i) => ({ n: i + 1, percent: a.total ? Math.round((a.correctCount / a.total) * 100) : 0, date: a.finishedAt?.toISOString() ?? "" }));
  const recentWrong = await prisma.userAnswer.findMany({
    where: { isCorrect: false, attempt: { ...w, status: "FINISHED" } },
    orderBy: { answeredAt: "desc" },
    take: 10,
    select: { answeredAt: true, question: { select: { id: true, code: true, text: true } } },
  });
  return {
    totalTests: finished.length,
    ticketsDone: ticketsDone.length,
    accuracy: correct + wrong ? Math.round((correct / (correct + wrong)) * 100) : 0,
    answered: progressAgg._count,
    mistakesCount,
    recent: attempts.slice(0, 10),
    chart,
    saved: saved.map((s) => s.question),
    recentWrong,
  };
}
