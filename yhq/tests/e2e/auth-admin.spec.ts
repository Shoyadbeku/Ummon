import { expect, test } from "@playwright/test";
import { ADMIN, login, startTicket } from "./helpers";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

test("ro'yxatdan o'tish: mehmon natijalari hisobga o'tadi", async ({ page }) => {
  await startTicket(page, 5);
  await page.getByTestId("option").first().click();
  await page.getByTestId("check").click();
  await page.getByTestId("finish").click();
  await page.getByTestId("confirm-finish").click();
  await page.waitForURL(/\/natija\//);

  const email = `user${Date.now()}@test.uz`;
  await page.goto("/royxat");
  await page.fill("#name", "Test Foydalanuvchi");
  await page.fill("#email", email);
  await page.fill("#password", "parol12345");
  await page.click("button[type=submit]");
  await page.waitForURL(/\/kabinet/);
  await expect(page.getByText("Test Foydalanuvchi").first()).toBeVisible();
  await expect(page.getByText("Bilet №5").first()).toBeVisible();

  // Noto'g'ri parol
  await page.getByRole("button", { name: "Chiqish" }).click();
  await page.goto("/kirish");
  await page.fill("#email", email);
  await page.fill("#password", "notogri-parol");
  await page.click("button[type=submit]");
  await expect(page.locator("form [role=alert]")).toContainText("noto'g'ri");
});

test("admin: savol qo'shadi, tahrirlaydi va import qiladi", async ({ page }) => {
  await login(page, ADMIN.email, ADMIN.password);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Statistika" })).toBeVisible();

  await page.goto("/admin/savollar/yangi");
  await page.waitForLoadState("networkidle");
  const stamp = Date.now();
  const text = `E2E test savoli ${stamp}: piyodalar o'tish joyida qayrilib olish mumkinmi?`;
  await page.getByLabel("Mavzu *").selectOption("manyovr");
  await page.getByLabel("Savol matni *").fill(text);
  await page.getByLabel("Tushuntirish (nima uchun to'g'ri) *").fill("62-bandga ko'ra piyodalar o'tish joylarida qayrilib olish taqiqlanadi.");
  await page.getByLabel("A variant matni").fill("Mumkin");
  await page.getByLabel("B variant matni").fill("Taqiqlanadi");
  await page.getByLabel("C variant matni").fill("Faqat tunda mumkin");
  await page.getByLabel("B to'g'ri javob").check();
  await page.getByTestId("save-question").click();
  await expect(page.getByText("Saqlandi ✓")).toBeVisible();

  // Takroriy savolni aniqlash
  await page.goto("/admin/savollar/yangi");
  await page.waitForLoadState("networkidle");
  await page.getByLabel("Mavzu *").selectOption("manyovr");
  await page.getByLabel("Savol matni *").fill(text);
  await page.getByLabel("Tushuntirish (nima uchun to'g'ri) *").fill("Takroriy savol izohi matni");
  await page.getByLabel("A variant matni").fill("Mumkin");
  await page.getByLabel("B variant matni").fill("Taqiqlanadi");
  await page.getByLabel("C variant matni").fill("Faqat tunda mumkin");
  await page.getByLabel("B to'g'ri javob").check();
  await page.getByTestId("save-question").click();
  await expect(page.getByText("O'xshash savollar topildi")).toBeVisible();

  // Qidiruvda topiladi
  await page.goto("/admin/savollar");
  await page.waitForLoadState("networkidle");
  await page.getByPlaceholder("Matn, kod yoki YHQ bandi…").fill(`E2E test savoli ${stamp}`);
  await expect(page.locator("tbody tr")).toHaveCount(1);

  // CSV import: tahlil + import
  await page.goto("/admin/import");
  await page.waitForLoadState("networkidle");
  // Har safar noyob matnli fayl (oldingi ishga tushirishlardagi importlar bilan takrorlanmasligi uchun)
  const run = Date.now();
  const csv = [
    "text,option_a,option_b,option_c,correct,explanation,category,difficulty,rule_ref",
    `"Import testi ${run}: turar joy dahasida eng yuqori tezlik qancha?","10 km/soat","20 km/soat","40 km/soat",B,"78-bandga ko'ra 20 km/soat.",tezlik,EASY,YHQ 78-band`,
    `"Import ${run} — avtomagistral: orqaga harakatlanishga ruxsat bormi yoki yo'qmi","Mumkin","Taqiqlanadi","Faqat kechasi",B,"121-bandga ko'ra taqiqlanadi.",magistral,EASY,YHQ 121-band`,
    `"Import ${run}: to'g'ri javobi ko'rsatilmagan savol","Bir","Ikki",,,"Izoh bor",tezlik,EASY,`,
    `"O'zbekiston Respublikasi yo'llarida transport vositalarining qanday harakatlanish tartibi belgilangan?","Chap tomonlama","O'ng tomonlama","Yo'l turiga qarab har xil",B,"2-band",umumiy,EASY,YHQ 2-band`,
  ].join("\n");
  const file = path.join(mkdtempSync(path.join(tmpdir(), "yhq-")), "import.csv");
  writeFileSync(file, csv);
  await page.getByTestId("import-file").setInputFiles(file);
  await page.getByTestId("import-analyze").click();
  await expect(page.getByTestId("import-summary")).toContainText("To'g'ri: 2");
  await expect(page.getByTestId("import-summary")).toContainText("Xato: 1");
  await expect(page.getByTestId("import-summary")).toContainText("Takror: 1");
  await page.getByTestId("import-commit").click();
  await expect(page.getByText("Import qilindi: 2")).toBeVisible();
});
