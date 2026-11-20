import { test, expect } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import type { Day } from "../src/features/plan/api";
import { readCards, skipQuestions } from "./study-flow";
import { css, showReference } from "./reference";

test("Today opens the server's next task, credits completion and responds to a new budget", async ({
  page,
  context,
}, info) => {
  test.setTimeout(90000);
  await page.goto("/");
  await page
    .getByRole("combobox", { name: tr.onboarding.field })
    .selectOption("sinif-ogretmenligi");
  const response = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/v1/plan/today" && r.status() === 200,
  );
  await page.getByRole("button", { name: tr.onboarding.explore }).click();
  const fetched = await response;
  const original: Day = await fetched.json();
  const authorization = await fetched.request().headerValue("authorization");
  expect(
    (
      await page.request.post(
        new URL(fetched.url()).origin + "/fixtures/season-pass",
        { headers: { authorization: authorization! } },
      )
    ).ok(),
  ).toBe(true);
  const t = tr.today;
  await expect(
    page.getByRole("heading", { name: t.title(original.total) }),
  ).toBeVisible();
  const progress = page.getByRole("progressbar", { name: t.progress });
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
  const ref = await context.newPage();
  await showReference(
    ref,
    info.project.name === "desktop" ? "web-today" : "today",
  );
  const h1 = page.getByRole("heading", { name: t.title(original.total) });
  expect(await css(h1, ["font-size", "line-height"])).toEqual(
    await css(ref.locator("h1"), ["font-size", "line-height"]),
  );
  await ref.close();
  await expect(page.getByText(tr.photo.tile)).toBeVisible();
  await expect(page.getByText("Türkiye geneli deneme 1")).toHaveCount(0);
  if (info.project.name === "desktop")
    await expect(
      page.getByRole("heading", { name: t.priorities }),
    ).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("today.png") });
  await page.getByRole("link", { name: tr.account.settings }).click();
  await page.getByRole("button", { name: "30 dk" }).click();
  await page.getByRole("button", { name: tr.account.save }).click();
  await expect(page.getByText(tr.account.saved)).toBeVisible();
  const changed = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/v1/plan/today" && r.status() === 200,
  );
  await page.getByRole("button", { name: tr.nav.back }).click();
  const revised: Day = await (await changed).json();
  expect(revised.daily_minutes).toBe(30);
  expect(
    revised.tasks.reduce((sum, task) => sum + task.minutes, 0),
  ).toBeLessThanOrEqual(revised.mock_day ? 110 : 30);
  for (let i = 0; i < revised.total; i++) {
    await page
      .getByRole("button", { name: tr.controls.start, exact: true })
      .click();
    const task = revised.tasks[i]!;
    if (task.kind === "lesson") {
      await readCards(page);
      await skipQuestions(page, 2);
    } else if (task.kind === "topic_test") {
      await skipQuestions(page, task.count);
    } else {
      await page.getByRole("button", { name: t.finish }).click();
    }
    await expect(page).toHaveURL(/\/today$/);
    await expect(progress).toHaveAttribute(
      "aria-valuenow",
      String(Math.round(((i + 1) * 100) / revised.total)),
    );
  }
  await expect(page.getByText(t.allDone)).toBeVisible();
  await expect(page.getByText(t.streak(1))).toBeVisible();
  await page.reload();
  await expect(progress).toHaveAttribute("aria-valuenow", "100");
});
