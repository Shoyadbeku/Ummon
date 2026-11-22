import { notFound } from "next/navigation";
import { prisma } from "@/lib/db";
import { PageHeader } from "@/components/ui/misc";
import { TicketEditor } from "@/components/admin/ticket-editor";

export default async function EditTicket({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const t = await prisma.ticket.findUnique({
    where: { id },
    include: { questions: { orderBy: { position: "asc" }, include: { question: { select: { id: true, code: true, text: true } } } } },
  });
  if (!t) notFound();
  return (
    <div>
      <PageHeader title={`Bilet №${t.number}`} subtitle="Tarkibni o'zgartirish: aniq 10 ta savol" />
      <TicketEditor id={t.id} initial={{ number: t.number, title: t.title ?? "", isPublished: t.isPublished, questions: t.questions.map((q) => q.question) }} />
    </div>
  );
}
