import { prisma } from "@/lib/db";
import { PageHeader } from "@/components/ui/misc";
import { QuestionsTable } from "@/components/admin/questions-table";

export default async function AdminQuestions() {
  const categories = await prisma.category.findMany({ orderBy: { order: "asc" }, select: { slug: true, name: true } });
  return (
    <div>
      <PageHeader title="Savollar" subtitle="Savollarni qo'shish, tahrirlash, tekshiruv holatini boshqarish" />
      <QuestionsTable categories={categories} />
    </div>
  );
}
