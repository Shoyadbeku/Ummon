import { prisma } from "@/lib/db";
import { createSession, hashPassword } from "@/lib/auth";
import { apiError, handler, json, readJson } from "@/lib/api";
import { registerSchema } from "@/lib/validation";
import { getActor, mergeGuestIntoUser } from "@/lib/actor";
import { rateLimit } from "@/lib/rate-limit";

export const POST = handler(async (req: Request) => {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "local";
  if (!rateLimit(`register:${ip}`, 10, 60 * 60_000)) return apiError(429, "Juda ko'p urinish. Keyinroq qayta urinib ko'ring.");
  const data = registerSchema.parse(await readJson(req));
  const exists = await prisma.user.findUnique({ where: { email: data.email } });
  if (exists) return apiError(409, "Bu elektron pochta bilan hisob mavjud");
  const actor = await getActor();
  const user = await prisma.user.create({
    data: { name: data.name, email: data.email, passwordHash: await hashPassword(data.password) },
  });
  if (actor.guestId) await mergeGuestIntoUser(actor.guestId, user.id);
  await createSession(user.id, req.headers.get("user-agent"));
  return json({ ok: true, user: { id: user.id, name: user.name, email: user.email, role: user.role } }, 201);
});
