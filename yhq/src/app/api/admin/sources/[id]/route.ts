import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { sourceSchema } from "@/lib/validation";
import { audit } from "@/lib/admin/questions";

type Ctx = { params: Promise<{ id: string }> };

export const PUT = handler(async (req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const d = sourceSchema.parse(await readJson(req));
  const s = await prisma.questionSource.update({ where: { id }, data: { ...d, url: d.url || null } });
  await audit(admin.id, "update", "source", id);
  return json(s);
});

export const DELETE = handler(async (_req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  await prisma.questionSource.delete({ where: { id } });
  await audit(admin.id, "delete", "source", id);
  return json({ ok: true });
});
