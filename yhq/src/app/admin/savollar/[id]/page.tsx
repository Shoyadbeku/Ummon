import { notFound } from "next/navigation";
import { prisma } from "@/lib/db";
import { PageHeader } from "@/components/ui/misc";
import { QuestionForm } from "@/components/admin/question-form";

export default async function EditQuestion({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ saved?: string }> }) {
  const { id } = await params;
  const { saved } = await searchParams;
  const [q, categories, sources] = await Promise.all([
    prisma.question.findUnique({ where: { id }, include: { options: { orderBy: { order: "asc" } }, category: { select: { slug: true } }, tickets: { select: { ticket: { select: { number: true } } } } } }),
    prisma.category.findMany({ orderBy: { order: "asc" }, select: { slug: true, name: true } }),
    prisma.questionSource.findMany({ select: { id: true, name: true, type: true, verified: true } }),
  ]);
  if (!q) notFound();
  return (
    <div>
      <PageHeader title={`Savol ${q.code}`} subtitle={`Oxirgi yangilanish: ${q.updatedAt.toISOString().slice(0, 16).replace("T", " ")}`} />
      {saved && <p className="mb-4 rounded-md bg-success-soft p-3 text-sm font-medium text-success" role="status">Saqlandi ✓</p>}
      <QuestionForm
        key={q.updatedAt.toISOString()}
        categories={categories}
        sources={sources}
        initial={{
          id: q.id, code: q.code, text: q.text, explanation: q.explanation, imageUrl: q.imageUrl ?? "", signCode: q.signCode ?? "",
          scene: q.scene ? JSON.stringify(q.scene, null, 2) : "", categorySlug: q.category.slug, difficulty: q.difficulty, sourceId: q.sourceId ?? "",
          ruleRef: q.ruleRef ?? "", ruleUrl: q.ruleUrl ?? "", origin: q.origin, verificationStatus: q.verificationStatus, isActive: q.isActive,
          reviewNote: q.reviewNote ?? "", options: q.options.map((o) => ({ text: o.text, isCorrect: o.isCorrect, explanation: o.explanation ?? "" })),
          tickets: q.tickets.map((t) => t.ticket.number).sort((a, b) => a - b),
        }}
      />
    </div>
  );
}
