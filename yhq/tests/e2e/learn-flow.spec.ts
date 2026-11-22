import { expect, test } from "@playwright/test";
import { startTicket } from "./helpers";

test("biletlar sahifasi: har bir biletda 10 ta savol", async ({ page }) => {
  await page.goto("/biletlar");
  const cards = page.locator("[data-testid^=ticket-]");
  expect(await cards.count()).toBeGreaterThanOrEqual(20);
  await expect(cards.first()).toContainText("10");
  await expect(cards.first()).toContainText("Hali ishlanmagan");
});

test("o'quv rejimi: javob, tekshirish, modal, yakunlash, natija va xatolar", async ({ page }) => {
  await startTicket(page, 1);
  await expect(page.getByTestId("question-counter")).toHaveText(/Savol №1 \/ 10/);

  // Variant tanlanmasa ogohlantirish
  await page.getByTestId("check").click();
  await expect(page.getByText("Avval javob variantini tanlang")).toBeVisible();

  // 1-savol: to'g'ri javobni modal orqali ko'rish
  await page.getByTestId("show-answer").click();
  const modal = page.getByTestId("answer-modal");
  await expect(modal).toBeVisible();
  await expect(modal).toContainText("TO'G'RI JAVOB");
  await expect(modal).toContainText("Nima uchun bu javob to'g'ri");
  await expect(modal).toContainText(/YHQ/);
  await page.getByRole("button", { name: "Keyingi savol" }).click();
  await expect(page.getByTestId("question-counter")).toHaveText(/Savol №2/);

  // Qolgan savollar: birinchi variantni tanlab tekshirish (klaviatura orqali ham)
  for (let i = 2; i <= 10; i++) {
    if (i % 2 === 0) {
      await page.getByTestId("option").first().click();
      await page.getByTestId("check").click();
    } else {
      await page.keyboard.press("1");
      await page.keyboard.press("Enter");
    }
    await expect(page.getByTestId("feedback")).toBeVisible();
    if (i < 10) await page.keyboard.press("ArrowRight");
  }

  await page.getByTestId("finish").click();
  await page.getByTestId("confirm-finish").click();
  await page.waitForURL(/\/natija\//);
  await expect(page.getByTestId("result-card")).toBeVisible();
  const correct = Number(await page.getByTestId("result-correct").innerText());
  const wrong = Number(await page.getByTestId("result-wrong").innerText());
  expect(correct + wrong).toBe(10);
  expect(wrong).toBeGreaterThanOrEqual(1); // 1-savol oldindan ko'rilgani uchun xato hisoblanadi
  await expect(page.getByTestId("result-percent")).toHaveText(`${correct * 10}%`);

  // Bilet holati yangilangan
  await page.goto("/biletlar");
  await expect(page.getByTestId("ticket-1")).toContainText(correct === 10 ? "Muvaffaqiyatli" : "Xatolar bilan");
  await expect(page.getByTestId("ticket-1")).toContainText(`${correct}/10`);

  // Xatolar saqlangan
  await page.goto("/xatolar");
  await expect(page.getByTestId("mistake-list").locator("li")).toHaveCount(wrong);
  await page.getByTestId("practice-mistakes").click();
  await page.waitForURL(/\/test\//);
  await expect(page.getByTestId("question-text")).toBeVisible();
});

test("tekshirilgan javob o'zgartirilmaydi", async ({ page }) => {
  await startTicket(page, 2);
  await page.getByTestId("option").nth(0).click();
  await page.getByTestId("check").click();
  await expect(page.getByTestId("feedback")).toBeVisible();
  await expect(page.getByTestId("option").nth(1)).toBeDisabled();
});
