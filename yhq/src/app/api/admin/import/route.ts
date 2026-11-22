import { requireAdmin } from "@/lib/auth";
import { apiError, handler, json } from "@/lib/api";
import { analyzeRows, parseFile } from "@/lib/admin/import";
import { audit, createQuestion } from "@/lib/admin/questions";

const MAX = 5 * 1024 * 1024;

/** multipart: file, commit=0|1. commit=0 — faqat tahlil (preview), commit=1 — to'g'ri va takror bo'lmagan qatorlar saqlanadi */
export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const form = await req.formData();
  const file = form.get("file");
  if (!(file instanceof File)) return apiError(400, "Fayl tanlanmagan");
  if (file.size > MAX) return apiError(413, "Fayl hajmi 5 MB dan oshmasligi kerak");
  let rows;
  try {
    rows = await parseFile(file.name, Buffer.from(await file.arrayBuffer()));
  } catch (e) {
    return apiError(400, (e as Error).message);
  }
  if (rows.length > 5000) return apiError(400, "Bir martada ko'pi bilan 5000 ta qator");
  const analysis = await analyzeRows(rows);
  const summary = {
    total: analysis.length,
    ok: analysis.filter((r) => r.status === "ok").length,
    invalid: analysis.filter((r) => r.status === "invalid").length,
    duplicate: analysis.filter((r) => r.status === "duplicate").length,
    imported: 0,
  };
  if (form.get("commit") === "1") {
    for (const r of analysis) {
      if (r.status !== "ok" || !r.input) continue;
      await createQuestion(r.input);
      summary.imported++;
    }
    await audit(admin.id, "import", "question", undefined, { file: file.name, ...summary });
  }
  return json({ summary, rows: analysis.map(({ input: _i, ...r }) => r) });
});
