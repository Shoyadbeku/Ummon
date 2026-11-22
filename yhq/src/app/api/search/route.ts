import { prisma } from "@/lib/db";
import { handler, json } from "@/lib/api";
import { getSettings, visibleQuestionWhere } from "@/lib/settings";

export const dynamic = "force-dynamic";

export const GET = handler(async (req: Request) => {
  const q = new URL(req.url).searchParams.get("q")?.trim().slice(0, 100) ?? "";
  if (q.length < 2) return json({ results: [] });
  const settings = await getSettings();
  const results = await prisma.question.findMany({
    where: {
      ...visibleQuestionWhere(settings),
      OR: [
        { text: { contains: q, mode: "insensitive" } },
        { explanation: { contains: q, mode: "insensitive" } },
        { ruleRef: { contains: q, mode: "insensitive" } },
        { code: { equals: q.toUpperCase() } },
        { options: { some: { text: { contains: q, mode: "insensitive" } } } },
      ],
    },
    take: 30,
    orderBy: { code: "asc" },
    select: {
      id: true, code: true, text: true, ruleRef: true, signCode: true,
      category: { select: { name: true, slug: true } },
      options: { where: { isCorrect: true }, select: { text: true } },
      tickets: { select: { ticket: { select: { number: true } } } },
    },
  });
  return json({
    results: results.map((r) => ({
      id: r.id, code: r.code, text: r.text, ruleRef: r.ruleRef, signCode: r.signCode, category: r.category,
      correct: r.options[0]?.text ?? null,
      tickets: r.tickets.map((t) => t.ticket.number),
    })),
  });
});
