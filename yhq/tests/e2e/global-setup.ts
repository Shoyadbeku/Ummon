import { execSync } from "node:child_process";

/**
 * Test bazasini tayyorlash: migratsiyalar (buzmaydigan `migrate deploy`) va seed (idempotent).
 * Testlar mavjud ma'lumotlarga bog'liq emas: har bir test yangi mehmon/foydalanuvchi va noyob matnlar bilan ishlaydi.
 */
export default async function globalSetup() {
  const url = process.env.TEST_DATABASE_URL ?? "postgresql://yhq:yhq@localhost:5432/yhq_test?schema=public";
  const env = { ...process.env, DATABASE_URL: url };
  execSync("npx prisma migrate deploy", { env, stdio: "inherit" });
  execSync("npx tsx prisma/seed.ts", { env, stdio: "inherit" });
}
