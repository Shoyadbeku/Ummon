import "server-only";
import { cookies } from "next/headers";
import { getCurrentUser, type SafeUser } from "./auth";
import { GUEST_COOKIE } from "./session-constants";
import { prisma } from "./db";

/** Joriy foydalanuvchi yoki mehmon (brauzer cookie identifikatori) */
export type Actor = { user: SafeUser | null; guestId: string | null };

const GUEST_RE = /^[a-f0-9-]{36}$/;

export async function getActor(): Promise<Actor> {
  const user = await getCurrentUser();
  if (user) return { user, guestId: null };
  const jar = await cookies();
  const gid = jar.get(GUEST_COOKIE)?.value ?? null;
  return { user: null, guestId: gid && GUEST_RE.test(gid) ? gid : null };
}

/** Prisma `where` filtri: shu aktorga tegishli yozuvlar */
export function actorWhere(actor: Actor): { userId: string } | { guestId: string } | null {
  if (actor.user) return { userId: actor.user.id };
  if (actor.guestId) return { guestId: actor.guestId };
  return null;
}

/** Mehmon sifatida ishlangan natijalarni ro'yxatdan o'tgan hisobga o'tkazish */
export async function mergeGuestIntoUser(guestId: string, userId: string) {
  await prisma.$transaction(async (tx) => {
    await tx.testAttempt.updateMany({ where: { guestId }, data: { userId, guestId: null } });
    const guestProgress = await tx.userProgress.findMany({ where: { guestId } });
    for (const gp of guestProgress) {
      const existing = await tx.userProgress.findUnique({ where: { userId_questionId: { userId, questionId: gp.questionId } } });
      if (existing) {
        const newer = (gp.lastAnsweredAt?.getTime() ?? 0) > (existing.lastAnsweredAt?.getTime() ?? 0);
        await tx.userProgress.update({
          where: { id: existing.id },
          data: {
            seenCount: existing.seenCount + gp.seenCount,
            correctCount: existing.correctCount + gp.correctCount,
            wrongCount: existing.wrongCount + gp.wrongCount,
            ...(newer ? { lastCorrect: gp.lastCorrect, inMistakes: gp.inMistakes, streak: gp.streak, lastAnsweredAt: gp.lastAnsweredAt } : {}),
          },
        });
        await tx.userProgress.delete({ where: { id: gp.id } });
      } else {
        await tx.userProgress.update({ where: { id: gp.id }, data: { userId, guestId: null } });
      }
    }
    const saved = await tx.savedQuestion.findMany({ where: { guestId } });
    for (const s of saved) {
      const exists = await tx.savedQuestion.findUnique({ where: { userId_questionId: { userId, questionId: s.questionId } } });
      if (exists) await tx.savedQuestion.delete({ where: { id: s.id } });
      else await tx.savedQuestion.update({ where: { id: s.id }, data: { userId, guestId: null } });
    }
  });
}
