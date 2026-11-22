import { expect, test } from "@playwright/test";

test("mobil: test sahifasi ekranga sig'adi va boshqaruv tugmalari ko'rinadi", async ({ page }) => {
  await page.goto("/biletlar");
  await page.click("[data-testid=start-learn-3]");
  await page.waitForURL(/\/test\//);
  await expect(page.getByTestId("question-text")).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  await expect(page.getByTestId("check")).toBeInViewport();
  await expect(page.getByTestId("finish")).toBeInViewport();
  await page.getByTestId("option").first().tap();
  await page.getByTestId("check").tap();
  await expect(page.getByTestId("feedback")).toBeVisible();
  await page.getByTestId("show-answer").tap();
  await expect(page.getByTestId("answer-modal")).toBeInViewport();
});

test("mobil: menyu ochiladi", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Menyu" }).tap();
  await page.getByRole("navigation", { name: "Mobil" }).getByRole("link", { name: "Yo'l belgilari" }).tap();
  await expect(page).toHaveURL(/\/belgilar/);
  await expect(page.getByText("2.1").first()).toBeVisible();
});
