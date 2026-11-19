import { expect, test } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import { readCards } from "./study-flow";
import { css, showReference } from "./reference";
import type { Lesson, Practice } from "../src/features/study/api";

test("Today leads through a lesson, answer, feedback, remedial card and earned completion", async ({
  page,
  context,
}, info) => {
  const t = tr.study;
  await page.goto("/");
  await page
    .getByRole("combobox", { name: tr.onboarding.field })
    .selectOption("sinif-ogretmenligi");
  await page.getByRole("button", { name: tr.onboarding.explore }).click();
  const detail = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname.startsWith("/v1/lessons/") &&
      r.status() === 200,
  );
  await page
    .getByRole("button", { name: tr.controls.start, exact: true })
    .click();
  const lesson: Lesson = await (await detail).json();
  const heading = page.getByRole("heading", {
    name: lesson.cards[0]!.title,
    exact: true,
  });
  await expect(heading).toBeVisible();
  const ref = await context.newPage();
  await showReference(ref, "micro-lesson");
  expect(await css(heading, ["font-size", "line-height"])).toEqual(
    await css(ref.locator("h1"), ["font-size", "line-height"]),
  );
  await page.screenshot({ path: info.outputPath("lesson.png") });
  const started = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/v1/practice-sessions" &&
      r.request().method() === "POST",
  );
  await readCards(page);
  const state: Practice = await (await started).json();
  expect(state.feedback).toBeNull();
  expect(Object.keys(state.question!).sort()).toEqual([
    "id",
    "options",
    "stem",
  ]);
  await expect(
    page.getByRole("button", { name: tr.placement.next }),
  ).toBeDisabled();
  await page.getByRole("button", { name: /^A\) / }).click();
  await page.getByRole("checkbox", { name: tr.placement.unsure }).click();
  const answered = page.waitForResponse((r) =>
    new URL(r.url()).pathname.endsWith("/answers"),
  );
  await page.getByRole("button", { name: tr.placement.next }).click();
  const f = ((await (await answered).json()) as Practice).feedback!;
  expect(f.is_correct).toBe(false);
  await expect(
    page.getByText(f.rationales[0]!.text, { exact: true }),
  ).toBeVisible();
  await showReference(ref, "question-review");
  const why = page.getByRole("heading", { name: t.whyWrong });
  expect(await css(why, ["font-size", "line-height"])).toEqual(
    await css(ref.locator("h1"), ["font-size", "line-height"]),
  );
  await page.screenshot({ path: info.outputPath("feedback.png") });
  await ref.close();
  await page.reload();
  await expect(why).toBeVisible();
  await page.getByRole("button", { name: t.report }).click();
  await page
    .getByRole("textbox", { name: t.reportPrompt })
    .fill("Örnek sorunun açıklamasını kontrol eder misiniz?");
  await page.getByRole("button", { name: t.send }).click();
  await expect(page.getByText(t.thanks)).toBeVisible();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await expect(
    page.getByRole("heading", {
      name: lesson.cards[f.card_position! - 1]!.title,
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await expect(
    page.getByRole("progressbar", { name: tr.placement.progress }),
  ).toHaveAttribute("aria-valuenow", "2");
  await page.getByRole("button", { name: tr.placement.blank }).click();
  await expect(page).toHaveURL(/\/today$/);
  await expect(
    page.getByRole("progressbar", { name: tr.today.progress }),
  ).toHaveAttribute("aria-valuenow", "33");
});

test("the law source sheet and quantitative feedback render the imported text", async ({
  page,
}, info) => {
  await page.goto("/lessons/lesson.legislation.firsat-ve-imkan-esitligi");
  await page.getByRole("button", { name: tr.study.articleText }).click();
  await expect(page.getByText(/Madde 4\s+Eğitim kurumları/)).toBeVisible();
  await page.getByRole("button", { name: tr.study.close }).click();
  await page.getByRole("button", { name: tr.study.nextCard }).click();
  await page.getByRole("button", { name: tr.study.nextCard }).click();
  await expect(
    page.getByText(tr.study.kinds.confused, { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: info.outputPath("law-card.png") });
  await page.getByRole("button", { name: tr.study.backLessons }).click();
  await expect(page).toHaveURL(/\/lessons$/);
  const topic = page
    .getByText("Yüzde ve oran problemleri", { exact: true })
    .locator("..");
  await topic.getByRole("button", { name: tr.study.beginTest }).click();
  for (const n of [1, 2]) {
    await expect(
      page.getByRole("progressbar", { name: tr.placement.progress }),
    ).toHaveAttribute("aria-valuenow", String(n));
    await page.getByRole("button", { name: tr.placement.blank }).click();
  }
  await expect(
    page.getByRole("progressbar", { name: tr.placement.progress }),
  ).toHaveAttribute("aria-valuenow", "3");
  await page.getByRole("button", { name: /^B\) / }).click();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await expect(
    page.getByRole("heading", { name: tr.study.whyRight }),
  ).toBeVisible();
  const line = page.getByText("N = 2,5 / 0,1 = 25", { exact: true });
  await line.scrollIntoViewIfNeeded();
  await expect(line).toBeVisible();
  expect(
    await page
      .locator("body")
      .evaluate((e) => e.scrollWidth <= window.innerWidth),
  ).toBe(true);
  await page.screenshot({ path: info.outputPath("math.png"), fullPage: true });
});
