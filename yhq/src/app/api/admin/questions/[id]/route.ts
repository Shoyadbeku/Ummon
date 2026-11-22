import { prisma } from "@/lib/db";
import { requireAdmin, HttpError } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { questionInputSchema } from "@/lib/validation";
import { audit, findDuplicates, updateQuestion } from "@/lib/admin/questions";

type Ctx = { params: Promise<{ id: string }> };

export const GET = handler(async (_req: Request, ctx: Ctx) => {
  await requireAdmin();
  const { id } = await ctx.params;
  const q = await prisma.question.findUnique({
    where: { id },
    include: { options: { orderBy: { order: "asc" } }, category: { select: { slug: true } }, tickets: { select: { ticket: { select: { number: true } } } } },
  });
  if (!q) throw new HttpError(404, "Savol topilmadi");
  return json(q);
});

export const PUT = handler(async (req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const body = (await readJson(req)) as Record<string, unknown>;
  const input = questionInputSchema.parse(body);
  if (!body.force) {
    const dups = await findDuplicates(input, id);
    if (dups.length) return json({ error: "O'xshash savol mavjud", duplicates: dups }, 409);
  }
  const q = await updateQuestion(id, input);
  await audit(admin.id, "update", "question", id, { code: q.code });
  return json(q);
});

export const DELETE = handler(async (_req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const q = await prisma.question.findUnique({ where: { id }, select: { code: true, _count: { select: { tickets: true } } } });
  if (!q) throw new HttpError(404, "Savol topilmadi");
  // Biletdagi savol o'chirilsa, bilet 10 tadan kam bo'lib qoladi — bunday biletlar nashrdan olinadi
  const affected = await prisma.ticketQuestion.findMany({ where: { questionId: id }, select: { ticketId: true } });
  await prisma.$transaction([
    prisma.question.delete({ where: { id } }),
    prisma.ticket.updateMany({ where: { id: { in: affected.map((a) => a.ticketId) } }, data: { isPublished: false } }),
  ]);
  await audit(admin.id, "delete", "question", id, { code: q.code, unpublishedTickets: affected.length });
  return json({ ok: true, unpublishedTickets: affected.length });
});
