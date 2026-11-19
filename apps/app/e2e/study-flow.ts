import { expect, type Page } from "@playwright/test";
import { tr } from "../src/i18n/tr";
export async function readCards(page: Page) {
  const progress = page.getByRole("progressbar", {
    name: tr.study.cardProgress,
  });
  await expect(progress).toBeVisible();
  const total = Number(await progress.getAttribute("aria-valuemax"));
  for (let n = 1; n < total; n++) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(n));
    await page.getByRole("button", { name: tr.study.nextCard }).click();
  }
  await page.getByRole("button", { name: tr.study.checks }).click();
}
export async function skipQuestions(page: Page, count: number) {
  const progress = page.getByRole("progressbar", {
    name: tr.placement.progress,
  });
  for (let n = 1; n <= count; n++) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(n));
    await page.getByRole("button", { name: tr.placement.blank }).click();
  }
}
