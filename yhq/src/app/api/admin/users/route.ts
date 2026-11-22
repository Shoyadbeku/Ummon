import { prisma } from "@/lib/db";
import { requireAdmin } from "@/lib/auth";
import { handler, json } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handler(async (req: Request) => {
  await requireAdmin();
  const q = new URL(req.url).searchParams.get("q")?.trim();
  const users = await prisma.user.findMany({
    where: q ? { OR: [{ email: { contains: q, mode: "insensitive" } }, { name: { contains: q, mode: "insensitive" } }] } : {},
    orderBy: { createdAt: "desc" },
    take: 200,
    select: { id: true, name: true, email: true, role: true, isBlocked: true, createdAt: true, _count: { select: { attempts: true } } },
  });
  return json(users);
});
