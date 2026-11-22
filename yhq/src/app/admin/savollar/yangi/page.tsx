import { prisma } from "@/lib/db";
import { PageHeader } from "@/components/ui/misc";
import { QuestionForm } from "@/components/admin/question-form";
import { EMPTY_QUESTION } from "@/components/admin/question-form-data";

export default async function NewQuestion() {
  const [categories, sources] = await Promise.all([
    prisma.category.findMany({ orderBy: { order: "asc" }, select: { slug: true, name: true } }),
    prisma.questionSource.findMany({ select: { id: true, name: true, type: true, verified: true } }),
  ]);
  return (
    <div>
      <PageHeader title="Yangi savol" />
      <QuestionForm initial={{ ...EMPTY_QUESTION, sourceId: sources.find((s) => s.type === "ORIGINAL_PRACTICE")?.id ?? "" }} categories={categories} sources={sources} />
    </div>
  );
}
