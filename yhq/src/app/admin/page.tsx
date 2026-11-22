import Link from "next/link";
import { prisma } from "@/lib/db";
import { Badge, Card, PageHeader, Stat } from "@/components/ui/misc";
import { AdminBarChart } from "@/components/admin/bar-chart";
import { percent } from "@/lib/utils";

export default async function AdminDashboard() {
  const since = new Date(Date.now() - 14 * 24 * 3600 * 1000);
  const [users, questions, tickets, attempts, finished, byStatus, byOrigin, recent, hardest, unpublished, logs] = await Promise.all([
    prisma.user.count(),
    prisma.question.count(),
    prisma.ticket.count(),
    prisma.testAttempt.count(),
    prisma.testAttempt.aggregate({ where: { status: "FINISHED" }, _sum: { correctCount: true, total: true }, _count: true }),
    prisma.question.groupBy({ by: ["verificationStatus"], _count: true }),
    prisma.question.groupBy({ by: ["origin"], _count: true }),
    prisma.testAttempt.findMany({ where: { startedAt: { gte: since } }, select: { startedAt: true } }),
    prisma.$queryRaw<{ id: string; code: string; text: string; total: bigint; wrong: bigint }[]>`
      SELECT q.id, q.code, q.text, COUNT(*) AS total, SUM(CASE WHEN a."isCorrect" THEN 0 ELSE 1 END) AS wrong
      FROM user_answers a JOIN questions q ON q.id = a."questionId"
      GROUP BY q.id HAVING COUNT(*) >= 3 ORDER BY (SUM(CASE WHEN a."isCorrect" THEN 0 ELSE 1 END)::float / COUNT(*)) DESC LIMIT 8`,
    prisma.ticket.count({ where: { isPublished: false } }),
    prisma.auditLog.findMany({ orderBy: { createdAt: "desc" }, take: 8, include: { user: { select: { name: true } } } }),
  ]);
  const days: { label: string; value: number }[] = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000);
    const key = d.toISOString().slice(0, 10);
    days.push({ label: key.slice(5), value: recent.filter((r) => r.startedAt.toISOString().slice(0, 10) === key).length });
  }
  const acc = percent(finished._sum.correctCount ?? 0, finished._sum.total ?? 0);
  return (
    <div className="space-y-6">
      <PageHeader title="Statistika" subtitle="Platforma bo'yicha umumiy ko'rsatkichlar" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Foydalanuvchilar" value={users} />
        <Stat label="Savollar" value={questions} />
        <Stat label="Biletlar" value={tickets} />
        <Stat label="Testlar (jami)" value={attempts} />
        <Stat label="O'rtacha natija" value={`${acc}%`} tone="accent" />
      </div>
      {unpublished > 0 && (
        <Card className="border-warning/40 bg-warning-soft/60 p-4 text-sm">
          {unpublished} ta bilet nashrdan olingan (savollar soni 10 ta emas yoki qo'lda o'chirilgan). <Link href="/admin/biletlar" className="font-semibold text-accent">Biletlarni ko'rish →</Link>
        </Card>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-5"><h2 className="mb-3 font-semibold">Oxirgi 14 kundagi testlar</h2><AdminBarChart data={days} /></Card>
        <Card className="p-5">
          <h2 className="mb-3 font-semibold">Savollar bazasi holati</h2>
          <div className="space-y-2 text-sm">
            {byStatus.map((s) => <div key={s.verificationStatus} className="flex justify-between"><Badge tone={s.verificationStatus === "VERIFIED" ? "success" : s.verificationStatus === "REJECTED" ? "danger" : "warning"}>{s.verificationStatus}</Badge><span className="font-semibold">{s._count}</span></div>)}
            <div className="my-2 border-t" />
            {byOrigin.map((s) => <div key={s.origin} className="flex justify-between"><span>{s.origin === "OFFICIAL" ? "Rasmiy" : "Mashq (mustaqil)"}</span><span className="font-semibold">{s._count}</span></div>)}
          </div>
        </Card>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h2 className="mb-3 font-semibold">Eng ko'p xato qilinadigan savollar</h2>
          {hardest.length === 0 ? <p className="text-sm text-muted-foreground">Ma'lumot yetarli emas.</p> : (
            <ul className="divide-y text-sm">
              {hardest.map((h) => (
                <li key={h.id} className="flex gap-3 py-2">
                  <Link href={`/admin/savollar/${h.id}`} className="shrink-0 font-mono text-accent">{h.code}</Link>
                  <span className="line-clamp-1 flex-1">{h.text}</span>
                  <Badge tone="danger">{percent(Number(h.wrong), Number(h.total))}%</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card className="p-5">
          <h2 className="mb-3 font-semibold">So'nggi amallar (audit)</h2>
          <ul className="divide-y text-sm">
            {logs.map((l) => <li key={l.id} className="py-2"><span className="text-muted-foreground">{l.createdAt.toISOString().slice(0, 16).replace("T", " ")}</span> · {l.user?.name ?? "—"} · <b>{l.action}</b> {l.entity}</li>)}
            {logs.length === 0 && <li className="text-muted-foreground">Hozircha yo'q.</li>}
          </ul>
        </Card>
      </div>
    </div>
  );
}
