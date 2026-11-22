import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { questionInputSchema } from "@/lib/validation";
import { audit, createQuestion, findDuplicates } from "@/lib/admin/questions";

export const dynamic = "force-dynamic";

export const GET = handler(async (req: Request) => {
  await requireAdmin();
  const sp = new URL(req.url).searchParams;
  const q = sp.get("q")?.trim();
  const page = Math.max(1, Number(sp.get("page") ?? 1));
  const size = 25;
  const where: Prisma.QuestionWhereInput = {
    ...(q ? { OR: [{ text: { contains: q, mode: "insensitive" } }, { code: { contains: q, mode: "insensitive" } }, { ruleRef: { contains: q, mode: "insensitive" } }] } : {}),
    ...(sp.get("category") ? { category: { slug: sp.get("category")! } } : {}),
    ...(sp.get("status") ? { verificationStatus: sp.get("status") as never } : {}),
    ...(sp.get("origin") ? { origin: sp.get("origin") as never } : {}),
    ...(sp.get("active") ? { isActive: sp.get("active") === "1" } : {}),
  };
  const [total, items] = await Promise.all([
    prisma.question.count({ where }),
    prisma.question.findMany({
      where, orderBy: { code: "asc" }, skip: (page - 1) * size, take: size,
      select: { id: true, code: true, text: true, origin: true, verificationStatus: true, isActive: true, difficulty: true, updatedAt: true, ruleRef: true, category: { select: { name: true } }, _count: { select: { tickets: true } } },
    }),
  ]);
  return json({ total, page, pages: Math.ceil(total / size), items });
});

export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const body = (await readJson(req)) as Record<string, unknown>;
  const input = questionInputSchema.parse(body);
  if (!body.force) {
    const dups = await findDuplicates(input);
    if (dups.length) return json({ error: "O'xshash savol mavjud", duplicates: dups }, 409);
  }
  const q = await createQuestion(input);
  await audit(admin.id, "create", "question", q.id, { code: q.code });
  return json(q, 201);
});
