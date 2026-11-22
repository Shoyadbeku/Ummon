import { prisma } from "@/lib/db";
import { Card, PageHeader } from "@/components/ui/misc";
import { ImportClient } from "@/components/admin/import-client";

export default async function ImportPage() {
  const cats = await prisma.category.findMany({ orderBy: { order: "asc" }, select: { slug: true, name: true } });
  return (
    <div className="space-y-5">
      <PageHeader title="Savollarni import qilish" subtitle="CSV, Excel (.xlsx) yoki JSON fayl. Avval tahlil qilinadi, keyin faqat to'g'ri va takrorlanmagan savollar saqlanadi." />
      <ImportClient />
      <Card className="p-5 text-sm">
        <h2 className="font-semibold">Fayl formati</h2>
        <p className="mt-2 text-muted-foreground">Ustunlar (CSV/XLSX birinchi qatori yoki JSON maydonlari):</p>
        <code className="mt-2 block overflow-x-auto rounded bg-muted p-3 text-xs">code, text, option_a, option_b, option_c, option_d, option_e, correct, explanation, category, difficulty, rule_ref, rule_url, origin, source_id, image_url, sign_code, verification</code>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-muted-foreground">
          <li><b>correct</b> — to'g'ri javob harfi (A–E). JSON uchun <code>options: [{"{"}text, isCorrect, explanation{"}"}]</code> ham mumkin.</li>
          <li><b>category</b> — mavzu kodi: {cats.map((c) => c.slug).join(", ")}</li>
          <li><b>origin</b> — PRACTICE (standart) yoki OFFICIAL. OFFICIAL uchun <b>source_id</b> majburiy.</li>
          <li>Takrorlar bazadagi va fayl ichidagi savollar bo'yicha aniqlanadi (aynan bir xil yoki ≥85% o'xshash).</li>
        </ul>
        <a href="/samples/savollar-namuna.csv" className="mt-3 inline-block font-semibold text-accent hover:underline">Namuna CSV faylni yuklab olish</a>
      </Card>
    </div>
  );
}
