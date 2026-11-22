import "server-only";
import type { Prisma } from "@prisma/client";
import { prisma } from "../db";
import { HttpError } from "../auth";
import { textHash, similarity, DUPLICATE_THRESHOLD } from "../normalize";
import type { QuestionInput } from "../validation";

export function hashFor(input: Pick<QuestionInput, "text" | "options">) {
  return textHash(input.text + " " + input.options.map((o) => o.text).join(" "));
}

/** Takroriy savollarni aniqlash: aynan bir xil (xesh) yoki matni juda o'xshash */
export async function findDuplicates(input: Pick<QuestionInput, "text" | "options">, excludeId?: string) {
  const hash = hashFor(input);
  const exact = await prisma.question.findMany({
    where: { textHash: hash, ...(excludeId ? { id: { not: excludeId } } : {}) },
    select: { id: true, code: true, text: true },
  });
  if (exact.length) return exact.map((q) => ({ ...q, score: 1 }));
  // O'xshashlik: kalit so'zlar bo'yicha nomzodlarni olib, Jaccard bilan baholash
  const words = input.text.split(/\s+/).filter((w) => w.length > 5).slice(0, 4);
  if (!words.length) return [];
  const candidates = await prisma.question.findMany({
    where: { OR: words.map((w) => ({ text: { contains: w, mode: "insensitive" as const } })), ...(excludeId ? { id: { not: excludeId } } : {}) },
    select: { id: true, code: true, text: true },
    take: 200,
  });
  return candidates
    .map((q) => ({ ...q, score: similarity(q.text, input.text) }))
    .filter((q) => q.score >= DUPLICATE_THRESHOLD)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
}

async function categoryId(slug: string) {
  const c = await prisma.category.findUnique({ where: { slug }, select: { id: true } });
  if (!c) throw new HttpError(400, `Mavzu topilmadi: ${slug}`);
  return c.id;
}

async function nextCode(tx: Prisma.TransactionClient) {
  const last = await tx.question.findFirst({ where: { code: { startsWith: "Q-" } }, orderBy: { code: "desc" }, select: { code: true } });
  const n = last ? parseInt(last.code.slice(2), 10) + 1 : 1;
  return `Q-${String(n).padStart(4, "0")}`;
}

function baseData(input: QuestionInput, catId: string) {
  return {
    text: input.text,
    explanation: input.explanation,
    imageUrl: input.imageUrl || null,
    signCode: input.signCode || null,
    scene: (input.scene ?? undefined) as Prisma.InputJsonValue | undefined,
    categoryId: catId,
    difficulty: input.difficulty,
    sourceId: input.sourceId || null,
    ruleRef: input.ruleRef || null,
    ruleUrl: input.ruleUrl || null,
    origin: input.origin,
    verificationStatus: input.verificationStatus,
    isActive: input.isActive,
    reviewNote: input.reviewNote || null,
    reviewedAt: input.verificationStatus === "VERIFIED" ? new Date() : null,
    textHash: hashFor(input),
  };
}

export async function createQuestion(input: QuestionInput) {
  const catId = await categoryId(input.categorySlug);
  return prisma.$transaction(async (tx) => {
    const code = input.code?.trim() || (await nextCode(tx));
    if (await tx.question.findUnique({ where: { code } })) throw new HttpError(409, `Kod band: ${code}`);
    return tx.question.create({
      data: {
        ...baseData(input, catId),
        code,
        options: { create: input.options.map((o, order) => ({ order, text: o.text, isCorrect: o.isCorrect, explanation: o.explanation || null })) },
      },
      select: { id: true, code: true },
    });
  });
}

export async function updateQuestion(id: string, input: QuestionInput) {
  const catId = await categoryId(input.categorySlug);
  const existing = await prisma.question.findUnique({ where: { id }, include: { options: { orderBy: { order: "asc" } } } });
  if (!existing) throw new HttpError(404, "Savol topilmadi");
  return prisma.$transaction(async (tx) => {
    // Variantlar: mavjudlari tartib bo'yicha yangilanadi (o'tgan javoblar tarixi saqlanadi), ortiqchalari o'chiriladi
    for (const [order, o] of input.options.entries()) {
      const prev = existing.options[order];
      if (prev) await tx.answerOption.update({ where: { id: prev.id }, data: { text: o.text, isCorrect: o.isCorrect, explanation: o.explanation || null } });
      else await tx.answerOption.create({ data: { questionId: id, order, text: o.text, isCorrect: o.isCorrect, explanation: o.explanation || null } });
    }
    if (existing.options.length > input.options.length) {
      await tx.answerOption.deleteMany({ where: { questionId: id, order: { gte: input.options.length } } });
    }
    return tx.question.update({
      where: { id },
      data: { ...baseData(input, catId), ...(input.code && input.code !== existing.code ? { code: input.code } : {}) },
      select: { id: true, code: true },
    });
  });
}

export async function audit(userId: string, action: string, entity: string, entityId?: string, details?: Prisma.InputJsonValue) {
  await prisma.auditLog.create({ data: { userId, action, entity, entityId, details } }).catch(() => {});
}
