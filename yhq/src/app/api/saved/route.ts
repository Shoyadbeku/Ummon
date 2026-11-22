import { z } from "zod";
import { prisma } from "@/lib/db";
import { handler, json, readJson } from "@/lib/api";
import { ensureActor } from "@/lib/attempts";

export const POST = handler(async (req: Request) => {
  const { questionId } = z.object({ questionId: z.string().min(1).max(40) }).parse(await readJson(req));
  const actor = await ensureActor();
  const q = await prisma.question.findUnique({ where: { id: questionId }, select: { id: true } });
  if (!q) return json({ error: "Savol topilmadi" }, 404);
  const where = actor.user
    ? { userId_questionId: { userId: actor.user.id, questionId } }
    : { guestId_questionId: { guestId: actor.guestId!, questionId } };
  const existing = await prisma.savedQuestion.findUnique({ where });
  if (existing) {
    await prisma.savedQuestion.delete({ where: { id: existing.id } });
    return json({ saved: false });
  }
  await prisma.savedQuestion.create({
    data: { questionId, ...(actor.user ? { userId: actor.user.id } : { guestId: actor.guestId! }) },
  });
  return json({ saved: true });
});
