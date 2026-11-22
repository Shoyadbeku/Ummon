import { z } from "zod";
import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { planTickets } from "@/lib/tickets";
import { getSettings, visibleQuestionWhere } from "@/lib/settings";
import { audit } from "@/lib/admin/questions";

/**
 * Biletlarni avtomatik qayta shakllantirish.
 * mode = "append": faqat hech bir biletga kirmagan savollardan yangi biletlar qo'shiladi (mavjudlari saqlanadi).
 * mode = "rebuild": barcha biletlar o'chirilib, savollar bazasidan qaytadan tuziladi (natijalar tarixi saqlanadi, bilet bog'lanishi uziladi).
 */
export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const { mode, seed } = z.object({ mode: z.enum(["append", "rebuild"]), seed: z.number().int().optional() }).parse(await readJson(req));
  const settings = await getSettings();
  const where = visibleQuestionWhere(settings);
  const candidates = await prisma.question.findMany({
    where: mode === "append" ? { ...where, tickets: { none: {} } } : where,
    select: { id: true, categoryId: true },
  });
  const plan = planTickets(candidates, seed ?? Date.now() % 100000);
  const result = await prisma.$transaction(async (tx) => {
    if (mode === "rebuild") await tx.ticket.deleteMany({});
    let next = ((await tx.ticket.aggregate({ _max: { number: true } }))._max.number ?? 0) + 1;
    for (const ids of plan.tickets) {
      await tx.ticket.create({ data: { number: next++, questions: { create: ids.map((questionId, position) => ({ questionId, position })) } } });
    }
    return { created: plan.tickets.length, leftover: plan.leftover.length };
  }, { timeout: 60_000 });
  await audit(admin.id, `generate-${mode}`, "ticket", undefined, result);
  return json(result);
});
