import { expect, type Page } from "@playwright/test";

export const ADMIN = { email: process.env.ADMIN_EMAIL ?? "admin@example.com", password: process.env.ADMIN_PASSWORD ?? "change-me-now-123" };

export async function login(page: Page, email: string, password: string) {
  await page.goto("/kirish");
  await page.fill("#email", email);
  await page.fill("#password", password);
  await page.click("button[type=submit]");
  await page.waitForURL((u) => !u.pathname.startsWith("/kirish"));
}

export async function startTicket(page: Page, n: number) {
  await page.goto("/biletlar");
  await page.click(`[data-testid=start-learn-${n}]`);
  await page.waitForURL(/\/test\//);
  await expect(page.getByTestId("question-text")).toBeVisible();
}
