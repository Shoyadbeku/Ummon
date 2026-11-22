import { expect, test } from "@playwright/test";

test("imtihon rejimi: javoblar test davomida oshkor qilinmaydi", async ({ page, request }) => {
  await page.goto("/imtihon");
  await page.getByTestId("start-exam").click();
  await page.waitForURL(/\/test\//);
  await expect(page.getByText("Imtihon rejimi", { exact: true })).toBeVisible();
  await expect(page.getByTestId("show-answer")).toHaveCount(0);
  await expect(page.getByText(/\d+:\d{2}/).first()).toBeVisible(); // taymer

  const id = page.url().split("/test/")[1];
  const view = await page.request.get(`/api/attempts/${id}`);
  const data = await view.json();
  expect(data.mode).toBe("EXAM");
  expect(data.questions).toHaveLength(20);
  expect(data.questions.every((q: { feedback: unknown }) => q.feedback === null)).toBe(true);
  expect(JSON.stringify(data)).not.toContain("isCorrect");

  // Javobni oldindan ko'rish taqiqlangan
  const reveal = await page.request.post(`/api/attempts/${id}/reveal`, { data: { questionId: data.questions[0].id } });
  expect(reveal.status()).toBe(403);

  // Javob saqlanadi, lekin to'g'riligi aytilmaydi
  const ans = await page.request.post(`/api/attempts/${id}/answer`, { data: { questionId: data.questions[0].id, optionId: data.questions[0].options[0].id } });
  expect((await ans.json()).feedback).toBeNull();

  // Boshqa brauzer (mehmon) bu testni ko'ra olmaydi
  const foreign = await request.get(`/api/attempts/${id}`);
  expect(foreign.status()).toBe(404);

  await page.getByTestId("finish").click();
  await page.getByTestId("confirm-finish").click();
  await page.waitForURL(/\/natija\//);
  await expect(page.getByText(/Imtihon (topshirildi|topshirilmadi)/)).toBeVisible();
  await expect(page.getByText("Ruxsat etilgan xatolar: 2")).toBeVisible();
});

test("admin API va sahifalar oddiy foydalanuvchiga yopiq", async ({ page, request }) => {
  expect((await request.get("/api/admin/questions")).status()).toBe(401);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/kirish/);
});

test("boshqa saytdan kelgan POST so'rov rad etiladi (CSRF)", async ({ request }) => {
  const r = await request.post("/api/attempts", { headers: { origin: "https://evil.example" }, data: { kind: "RANDOM" } });
  expect(r.status()).toBe(403);
});
