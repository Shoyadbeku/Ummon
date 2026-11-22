import { prisma } from "@/lib/db";
import { requireAdmin, HttpError } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { ticketCompositionSchema } from "@/lib/validation";
import { validateTicketComposition } from "@/lib/tickets";
import { audit } from "@/lib/admin/questions";

export const dynamic = "force-dynamic";

export const GET = handler(async () => {
  await requireAdmin();
  const tickets = await prisma.ticket.findMany({
    orderBy: { number: "asc" },
    select: { id: true, number: true, title: true, isPublished: true, updatedAt: true, _count: { select: { questions: true, attempts: true } } },
  });
  return json(tickets);
});

/** Yangi bilet yaratish (aniq 10 ta savol bilan) */
export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const data = ticketCompositionSchema.parse(await readJson(req));
  const err = validateTicketComposition(data.questionIds);
  if (err) throw new HttpError(400, err);
  const found = await prisma.question.count({ where: { id: { in: data.questionIds } } });
  if (found !== data.questionIds.length) throw new HttpError(400, "Ba'zi savollar topilmadi");
  const number = data.number ?? ((await prisma.ticket.aggregate({ _max: { number: true } }))._max.number ?? 0) + 1;
  if (await prisma.ticket.findUnique({ where: { number } })) throw new HttpError(409, `№${number} bilet mavjud`);
  const t = await prisma.ticket.create({
    data: { number, title: data.title ?? null, isPublished: data.isPublished ?? true, questions: { create: data.questionIds.map((questionId, position) => ({ questionId, position })) } },
  });
  await audit(admin.id, "create", "ticket", t.id, { number });
  return json(t, 201);
});
