import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { sourceSchema } from "@/lib/validation";
import { audit } from "@/lib/admin/questions";

export const dynamic = "force-dynamic";

export const GET = handler(async () => {
  await requireAdmin();
  return json(await prisma.questionSource.findMany({ orderBy: { createdAt: "asc" }, include: { _count: { select: { questions: true } } } }));
});

export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const d = sourceSchema.parse(await readJson(req));
  const s = await prisma.questionSource.create({ data: { ...d, url: d.url || null } });
  await audit(admin.id, "create", "source", s.id);
  return json(s, 201);
});
