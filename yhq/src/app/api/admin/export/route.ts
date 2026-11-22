import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler } from "@/lib/api";

/** Savollar bazasini JSON formatida eksport qilish (import formati bilan mos) */
export const GET = handler(async () => {
  await requireAdmin();
  const qs = await prisma.question.findMany({
    orderBy: { code: "asc" },
    include: { options: { orderBy: { order: "asc" } }, category: { select: { slug: true } } },
  });
  const out = qs.map((q) => ({
    code: q.code, text: q.text, explanation: q.explanation, category: q.category.slug, difficulty: q.difficulty,
    rule_ref: q.ruleRef, rule_url: q.ruleUrl, origin: q.origin, source_id: q.sourceId, image_url: q.imageUrl, sign_code: q.signCode,
    verification: q.verificationStatus,
    options: q.options.map((o) => ({ text: o.text, isCorrect: o.isCorrect, explanation: o.explanation })),
  }));
  return new Response(JSON.stringify(out, null, 2), {
    headers: { "content-type": "application/json; charset=utf-8", "content-disposition": `attachment; filename="yhq-savollar-${new Date().toISOString().slice(0, 10)}.json"` },
  });
});
