import { expect, test } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import { css, showReference } from "./reference";
test("timed mock saves across a reload and client clock change, then opens result, review and progress", async ({
  page,
  context,
}) => {
  const t = tr.mock;
  await page.goto("/mock");
  await page.getByRole("button", { name: t.timed }).first().click();
  await expect(page.getByText(t.left)).toBeVisible();
  const flag = page.getByRole("button", { name: t.flag, exact: true });
  await page.getByRole("button", { name: /^B\)/ }).click();
  await expect(page.getByRole("button", { name: /^B\)/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await flag.click();
  await page.getByRole("button", { name: t.next, exact: true }).click();
  await expect(page.getByText(t.count(2, 80, true))).toBeVisible();
  await page.clock.setFixedTime(new Date("2031-01-01T00:00:00Z"));
  await page.reload();
  await expect(page.getByText(t.count(2, 80, true))).toBeVisible();
  await page.getByRole("button", { name: /^1, .*sonra bak/ }).click();
  await expect(page.getByRole("button", { name: /^B\)/ })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  const ref = await context.newPage();
  await showReference(ref, "mock-exam");
  expect(await css(page.getByRole("progressbar"), ["height"])).toEqual(
    await css(ref.getByRole("progressbar"), ["height"]),
  );
  await page.screenshot({ path: test.info().outputPath("mock.png") });
  await page.getByRole("button", { name: t.finish }).click();
  await expect(page.getByText(t.confirm(79))).toBeVisible();
  await page.getByRole("button", { name: t.end, exact: true }).click();
  await expect(page).toHaveURL(/\/result$/);
  await expect(page.getByText(t.blank(79))).toBeVisible();
  await showReference(ref, "nationwide-result");
  expect(
    await css(page.getByRole("heading").first(), ["font-size", "line-height"]),
  ).toEqual(await css(ref.locator("h1"), ["font-size", "line-height"]));
  await page.getByRole("button", { name: t.all }).click();
  await expect(page.getByText(/^Kaynak · /)).toBeVisible();
  await page.getByRole("button", { name: t.result }).first().click();
  await page.getByRole("button", { name: t.growth }).click();
  await expect(page.getByText(tr.today.net)).toBeVisible();
  await expect(page.getByText(tr.progress.streak)).toBeVisible();
  await expect(page.getByText(/Haftalık lig/)).toHaveCount(0);
  await ref.close();
});
