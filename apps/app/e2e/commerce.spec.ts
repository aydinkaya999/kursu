import { expect, test } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import { formatCurrency, formatUntilDate } from "../src/lib/format";
import type { Offer } from "../src/features/commerce/api";
import { signUp } from "./email-flow";
import { css, showReference } from "./reference";

test("a free mock result leads to account checkout, replay and shared access", async ({
  page,
  context,
}) => {
  const t = tr.commerce;
  await page.goto("/mock");
  await page.getByRole("button", { name: tr.mock.practice }).first().click();
  await page.getByRole("button", { name: tr.mock.finish }).click();
  await page.getByRole("button", { name: tr.mock.end, exact: true }).click();
  await expect(page.getByText(t.mocks)).toBeVisible();
  const response = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/v1/paywall" && r.status() === 200,
  );
  await page.getByRole("button", { name: t.see }).click();
  const offer: Offer = await (await response).json();
  await expect(page.getByText(formatCurrency(offer.amount_try))).toBeVisible();
  await expect(
    page.getByText(t.valid(formatUntilDate(offer.results_date))),
  ).toBeVisible();
  await expect(page.getByRole("table", { name: t.features })).toContainText(
    t.first(offer.limits.plan_days),
  );
  await expect(page.getByText(t.disclaimer)).toBeVisible();
  const ref = await context.newPage();
  await showReference(ref, "paywall");
  expect(
    await css(page.getByRole("heading", { name: tr.notebook.passIntro }), [
      "font-size",
      "line-height",
    ]),
  ).toEqual(await css(ref.locator("h1"), ["font-size", "line-height"]));
  await ref.close();
  await page.screenshot({ path: test.info().outputPath("paywall.png") });
  await page.getByRole("button", { name: t.buy }).click();
  await signUp(page);
  await expect(page.getByText(formatCurrency(offer.amount_try))).toBeVisible();
  await page.getByRole("button", { name: t.buy }).click();
  await expect(page).toHaveURL(/\/mock\/[^/]+\/result$/);
  await expect(page.getByText(t.mocks)).toHaveCount(0);
  await page.goto("/mock");
  await page.getByRole("button", { name: tr.mock.timed }).nth(1).click();
  await expect(page.getByText(tr.mock.left)).toBeVisible();
});
test("a second distinct lesson opens the daily limit and returns to the library", async ({
  page,
}) => {
  await page.goto("/lessons");
  const lessons = page.getByRole("button", { name: /^\[ÖRNEK\].*ders/i });
  await lessons.first().click();
  await expect(
    page.getByRole("button", { name: tr.study.nextCard }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.study.backLessons }).click();
  await lessons.nth(1).click();
  await expect(page.getByText(tr.commerce.limit)).toBeVisible();
  await page.getByRole("button", { name: tr.commerce.tomorrow }).click();
  await expect(page).toHaveURL(/\/lessons$/);
});
