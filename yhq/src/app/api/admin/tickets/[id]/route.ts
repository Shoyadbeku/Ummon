import { prisma } from "@/lib/db";
import { requireAdmin, HttpError } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { ticketCompositionSchema } from "@/lib/validation";
import { validateTicketComposition } from "@/lib/tickets";
import { audit } from "@/lib/admin/questions";

type Ctx = { params: Promise<{ id: string }> };

export const GET = handler(async (_req: Request, ctx: Ctx) => {
  await requireAdmin();
  const { id } = await ctx.params;
  const t = await prisma.ticket.findUnique({
    where: { id },
    include: { questions: { orderBy: { position: "asc" }, include: { question: { select: { id: true, code: true, text: true, verificationStatus: true, isActive: true, category: { select: { name: true } } } } } } },
  });
  if (!t) throw new HttpError(404, "Bilet topilmadi");
  return json(t);
});

/** Bilet tarkibini o'zgartirish */
export const PUT = handler(async (req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const data = ticketCompositionSchema.parse(await readJson(req));
  const err = validateTicketComposition(data.questionIds);
  if (err) throw new HttpError(400, err);
  const found = await prisma.question.count({ where: { id: { in: data.questionIds } } });
  if (found !== data.questionIds.length) throw new HttpError(400, "Ba'zi savollar topilmadi");
  if (data.number) {
    const clash = await prisma.ticket.findFirst({ where: { number: data.number, id: { not: id } } });
    if (clash) throw new HttpError(409, `№${data.number} bilet mavjud`);
  }
  await prisma.$transaction([
    prisma.ticketQuestion.deleteMany({ where: { ticketId: id } }),
    prisma.ticket.update({
      where: { id },
      data: {
        ...(data.number ? { number: data.number } : {}),
        title: data.title ?? null,
        isPublished: data.isPublished ?? true,
        questions: { create: data.questionIds.map((questionId, position) => ({ questionId, position })) },
      },
    }),
  ]);
  await audit(admin.id, "update", "ticket", id);
  return json({ ok: true });
});

export const DELETE = handler(async (_req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  await prisma.ticket.delete({ where: { id } });
  await audit(admin.id, "delete", "ticket", id);
  return json({ ok: true });
});
