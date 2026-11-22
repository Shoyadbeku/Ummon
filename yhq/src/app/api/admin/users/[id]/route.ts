import { prisma } from "@/lib/db";
import { requireAdmin, HttpError } from "@/lib/auth";
import { handler, json, readJson } from "@/lib/api";
import { userPatchSchema } from "@/lib/validation";
import { audit } from "@/lib/admin/questions";

type Ctx = { params: Promise<{ id: string }> };

export const PATCH = handler(async (req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const data = userPatchSchema.parse(await readJson(req));
  if (id === admin.id && (data.role === "USER" || data.isBlocked)) throw new HttpError(400, "O'zingizni administratorlikdan chiqara yoki bloklay olmaysiz");
  const u = await prisma.user.update({ where: { id }, data, select: { id: true, role: true, isBlocked: true } });
  if (data.isBlocked) await prisma.session.deleteMany({ where: { userId: id } });
  await audit(admin.id, "update", "user", id, data);
  return json(u);
});

export const DELETE = handler(async (_req: Request, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  if (id === admin.id) throw new HttpError(400, "O'zingizni o'chira olmaysiz");
  await prisma.user.delete({ where: { id } });
  await audit(admin.id, "delete", "user", id);
  return json({ ok: true });
});
