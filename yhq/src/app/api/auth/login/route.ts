import { prisma } from "@/lib/db";
import { createSession, verifyPassword } from "@/lib/auth";
import { apiError, handler, json, readJson } from "@/lib/api";
import { loginSchema } from "@/lib/validation";
import { getActor, mergeGuestIntoUser } from "@/lib/actor";
import { rateLimit } from "@/lib/rate-limit";
import bcrypt from "bcryptjs";

// Vaqt bo'yicha hujumlarga qarshi: foydalanuvchi topilmasa ham bcrypt tekshiruvi bajariladi
let dummyHash: string | null = null;
async function getDummyHash() {
  dummyHash ??= await bcrypt.hash("timing-safe-dummy-password", 12);
  return dummyHash;
}

export const POST = handler(async (req: Request) => {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "local";
  const data = loginSchema.parse(await readJson(req));
  if (!rateLimit(`login:${ip}:${data.email}`, 8, 15 * 60_000)) {
    return apiError(429, "Juda ko'p urinish. 15 daqiqadan so'ng qayta urinib ko'ring.");
  }
  const user = await prisma.user.findUnique({ where: { email: data.email } });
  const ok = await verifyPassword(data.password, user?.passwordHash ?? (await getDummyHash()));
  if (!user || !ok) return apiError(401, "Elektron pochta yoki parol noto'g'ri");
  if (user.isBlocked) return apiError(403, "Hisob bloklangan");
  const actor = await getActor();
  if (actor.guestId) await mergeGuestIntoUser(actor.guestId, user.id);
  await createSession(user.id, req.headers.get("user-agent"));
  return json({ ok: true, user: { id: user.id, name: user.name, email: user.email, role: user.role } });
});
