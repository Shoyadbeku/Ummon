import "server-only";
import { prisma } from "./db";
import { z } from "zod";

export const settingsSchema = z.object({
  examQuestionCount: z.number().int().min(5).max(100),
  examTimeMinutes: z.number().int().min(1).max(180),
  examMaxErrors: z.number().int().min(0).max(50),
  /** Rasmiy imtihon formati amaldagi talablar bo'yicha tekshirilganmi */
  examFormatVerified: z.boolean(),
  examFormatNote: z.string().max(1000),
  /** Tekshirilmagan (mashq) savollarni foydalanuvchilarga ko'rsatish */
  includeUnverified: z.boolean(),
});

export type AppSettings = z.infer<typeof settingsSchema>;

export const DEFAULT_SETTINGS: AppSettings = {
  examQuestionCount: 20,
  examTimeMinutes: 25,
  examMaxErrors: 2,
  examFormatVerified: false,
  examFormatNote:
    "Standart qiymatlar (20 savol, 25 daqiqa, ko'pi bilan 2 xato) ochiq manbalardagi ma'lumotlarga asoslangan va rasmiy tasdiqlanmagan. Amaldagi talablarni DYHXX/IIV manbalaridan tekshirib, sozlamalarni yangilang.",
  includeUnverified: true,
};

export async function getSettings(): Promise<AppSettings> {
  const rows = await prisma.appSetting.findMany();
  const obj: Record<string, unknown> = { ...DEFAULT_SETTINGS };
  for (const r of rows) obj[r.key] = r.value;
  const parsed = settingsSchema.safeParse(obj);
  return parsed.success ? parsed.data : DEFAULT_SETTINGS;
}

export async function saveSettings(s: AppSettings) {
  await prisma.$transaction(
    Object.entries(s).map(([key, value]) =>
      prisma.appSetting.upsert({ where: { key }, create: { key, value }, update: { value } }),
    ),
  );
}

/** Foydalanuvchilarga ko'rsatiladigan savollar filtri */
export function visibleQuestionWhere(s: AppSettings) {
  return s.includeUnverified
    ? { isActive: true, verificationStatus: { not: "REJECTED" as const } }
    : { isActive: true, verificationStatus: "VERIFIED" as const };
}
