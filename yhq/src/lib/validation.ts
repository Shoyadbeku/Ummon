import { z } from "zod";

export const registerSchema = z.object({
  name: z.string().trim().min(2, "Ism kamida 2 ta belgi").max(80),
  email: z.string().trim().toLowerCase().email("Elektron pochta noto'g'ri").max(200),
  password: z.string().min(8, "Parol kamida 8 ta belgi").max(200),
});

export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email("Elektron pochta noto'g'ri").max(200),
  password: z.string().min(1).max(200),
});

export const startAttemptSchema = z.object({
  kind: z.enum(["TICKET", "EXAM", "RANDOM", "TOPIC", "MISTAKES", "SIGNS", "FAVORITES"]),
  mode: z.enum(["LEARN", "EXAM"]).default("LEARN"),
  ticketNumber: z.number().int().positive().optional(),
  categorySlug: z.string().max(60).optional(),
  count: z.number().int().min(5).max(50).optional(),
});

export const answerSchema = z.object({
  questionId: z.string().min(1).max(40),
  optionId: z.string().min(1).max(40),
});

export const revealSchema = z.object({ questionId: z.string().min(1).max(40) });

export const optionInputSchema = z.object({
  text: z.string().trim().min(1, "Variant matni bo'sh").max(1000),
  isCorrect: z.boolean(),
  explanation: z.string().trim().max(1000).optional().nullable(),
});

const sceneSchema = z.record(z.string(), z.unknown()).nullable().optional();

/** Savol yaratish/tahrirlash va import uchun yagona validatsiya */
export const questionInputSchema = z
  .object({
    code: z.string().trim().max(40).optional(),
    text: z.string().trim().min(5, "Savol matni juda qisqa").max(2000),
    explanation: z.string().trim().min(5, "Tushuntirish kiritilishi shart").max(4000),
    imageUrl: z.string().trim().max(500).optional().nullable(),
    signCode: z.string().trim().max(20).optional().nullable(),
    scene: sceneSchema,
    categorySlug: z.string().trim().min(1, "Mavzu ko'rsatilishi shart").max(60),
    difficulty: z.enum(["EASY", "MEDIUM", "HARD"]).default("MEDIUM"),
    sourceId: z.string().max(40).optional().nullable(),
    ruleRef: z.string().trim().max(200).optional().nullable(),
    ruleUrl: z.string().trim().url("Havola noto'g'ri").max(500).optional().nullable().or(z.literal("")),
    origin: z.enum(["OFFICIAL", "PRACTICE"]).default("PRACTICE"),
    verificationStatus: z.enum(["UNVERIFIED", "IN_REVIEW", "VERIFIED", "REJECTED"]).default("UNVERIFIED"),
    isActive: z.boolean().default(true),
    reviewNote: z.string().max(1000).optional().nullable(),
    options: z.array(optionInputSchema).min(2, "Kamida 2 ta javob varianti").max(6, "Ko'pi bilan 6 ta variant"),
  })
  .superRefine((q, ctx) => {
    const correct = q.options.filter((o) => o.isCorrect).length;
    if (correct !== 1) ctx.addIssue({ code: "custom", path: ["options"], message: "Aniq bitta to'g'ri javob belgilanishi shart" });
    const texts = q.options.map((o) => o.text.toLowerCase());
    if (new Set(texts).size !== texts.length) ctx.addIssue({ code: "custom", path: ["options"], message: "Javob variantlari takrorlanmasligi kerak" });
    if (q.origin === "OFFICIAL" && !q.sourceId) ctx.addIssue({ code: "custom", path: ["sourceId"], message: "Rasmiy savol uchun tasdiqlangan manba ko'rsatilishi shart" });
  });

export type QuestionInput = z.infer<typeof questionInputSchema>;

export const ticketCompositionSchema = z.object({
  number: z.number().int().positive().optional(),
  title: z.string().max(200).optional().nullable(),
  isPublished: z.boolean().optional(),
  questionIds: z.array(z.string().min(1).max(40)),
});

export const sourceSchema = z.object({
  name: z.string().trim().min(2).max(300),
  type: z.enum(["OFFICIAL_LAW", "OFFICIAL_QUESTION_BANK", "ORIGINAL_PRACTICE", "THIRD_PARTY"]),
  url: z.string().trim().url().max(500).optional().nullable().or(z.literal("")),
  license: z.string().max(500).optional().nullable(),
  notes: z.string().max(2000).optional().nullable(),
  verified: z.boolean().default(false),
});

export const userPatchSchema = z.object({
  role: z.enum(["USER", "ADMIN"]).optional(),
  isBlocked: z.boolean().optional(),
});
