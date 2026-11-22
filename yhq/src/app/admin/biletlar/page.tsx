import Link from "next/link";
import { prisma } from "@/lib/db";
import { Badge, Card, PageHeader } from "@/components/ui/misc";
import { buttonClass } from "@/components/ui/button";
import { GenerateTickets } from "@/components/admin/generate-tickets";

export default async function AdminTickets() {
  const [tickets, unassigned] = await Promise.all([
    prisma.ticket.findMany({ orderBy: { number: "asc" }, select: { id: true, number: true, title: true, isPublished: true, _count: { select: { questions: true, attempts: true } } } }),
    prisma.question.count({ where: { isActive: true, verificationStatus: { not: "REJECTED" }, tickets: { none: {} } } }),
  ]);
  return (
    <div>
      <PageHeader title="Biletlar" subtitle={`Jami ${tickets.length} ta bilet. Biletga kirmagan faol savollar: ${unassigned} ta.`}>
        <Link href="/admin/biletlar/yangi" className={buttonClass("accent")}>Yangi bilet</Link>
      </PageHeader>
      <GenerateTickets unassigned={unassigned} />
      <Card className="mt-5 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground"><tr><th className="p-3">№</th><th className="p-3">Savollar</th><th className="p-3">Holat</th><th className="p-3">Urinishlar</th><th className="p-3" /></tr></thead>
          <tbody className="divide-y">
            {tickets.map((t) => (
              <tr key={t.id}>
                <td className="p-3 font-semibold">№{t.number}{t.title ? ` — ${t.title}` : ""}</td>
                <td className="p-3"><Badge tone={t._count.questions === 10 ? "success" : "danger"}>{t._count.questions}/10</Badge></td>
                <td className="p-3"><Badge tone={t.isPublished ? "success" : "muted"}>{t.isPublished ? "Nashr etilgan" : "Yashirin"}</Badge></td>
                <td className="p-3">{t._count.attempts}</td>
                <td className="p-3 text-right"><Link className="font-semibold text-accent hover:underline" href={`/admin/biletlar/${t.id}`}>Tahrirlash</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
