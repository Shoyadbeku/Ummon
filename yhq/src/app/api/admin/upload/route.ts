import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";
import { requireAdmin } from "@/lib/auth";
import { apiError, handler, json } from "@/lib/api";
import { audit } from "@/lib/admin/questions";

const MAX = 8 * 1024 * 1024;
const ALLOWED = ["image/png", "image/jpeg", "image/webp", "image/gif"];

function uploadDir() {
  return path.resolve(process.env.UPLOAD_DIR || "./uploads");
}

/** Rasm yuklash: hajm va turi tekshiriladi, sharp bilan 1200px gacha kichraytirilib WebP ga o'tkaziladi */
export const POST = handler(async (req: Request) => {
  const admin = await requireAdmin();
  const form = await req.formData();
  const file = form.get("file");
  if (!(file instanceof File)) return apiError(400, "Fayl tanlanmagan");
  if (file.size > MAX) return apiError(413, "Fayl hajmi 8 MB dan oshmasligi kerak");
  if (!ALLOWED.includes(file.type)) return apiError(415, "Faqat PNG, JPG, WEBP yoki GIF");
  const input = Buffer.from(await file.arrayBuffer());
  let out: Buffer;
  try {
    out = await sharp(input).rotate().resize({ width: 1200, height: 1200, fit: "inside", withoutEnlargement: true }).webp({ quality: 82 }).toBuffer();
  } catch {
    return apiError(415, "Rasm faylini o'qib bo'lmadi");
  }
  const name = `${randomUUID()}.webp`;
  await mkdir(uploadDir(), { recursive: true });
  await writeFile(path.join(uploadDir(), name), out);
  await audit(admin.id, "upload", "image", name, { size: out.length });
  return json({ url: `/uploads/${name}` }, 201);
});
