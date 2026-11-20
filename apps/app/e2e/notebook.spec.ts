import { test, expect, type Page } from "@playwright/test";
import seed from "../../../content/seed/sample-content.json";
import { tr } from "../src/i18n/tr";
import type { Practice } from "../src/features/study/api";
import { css, showReference } from "./reference";
import { readCards } from "./study-flow";

const t = tr.notebook;

async function onboard(page: Page) {
  await page.goto("/");
  await page
    .getByRole("combobox", { name: tr.onboarding.field })
    .selectOption("sinif-ogretmenligi");
  const plan = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/v1/plan/today" && r.ok(),
  );
  await page.getByRole("button", { name: tr.onboarding.explore }).click();
  return plan;
}

test("a mistake opens the grouped notebook and a free review opens the pass screen", async ({
  page,
  context,
}, info) => {
  await onboard(page);
  await page.getByRole("link", { name: tr.nav.notebook, exact: true }).click();
  await expect(page.getByText(t.empty)).toBeVisible();
  await page.getByRole("button", { name: tr.nav.back }).click();
  await page
    .getByRole("button", { name: tr.controls.start, exact: true })
    .click();
  await readCards(page);
  await page.getByRole("button", { name: /^A\) / }).click();
  await page.getByRole("checkbox", { name: tr.placement.unsure }).click();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await page.getByRole("button", { name: t.saved(t.when(1)) }).click();
  await expect(page).toHaveURL(/\/notebook$/);
  const heading = page.getByRole("heading", {
    name: tr.nav.notebook,
    exact: true,
  });
  await expect(page.getByText(t.counts(1, 0))).toBeVisible();
  await expect(page.getByText(t.tomorrow(1))).toBeVisible();
  const section = page.getByRole("group", { name: t.status });
  const ref = await context.newPage();
  await showReference(ref, "mistake-notebook");
  expect(
    await css(heading, ["font-size", "line-height", "letter-spacing"]),
  ).toEqual(
    await css(ref.locator("h1"), [
      "font-size",
      "line-height",
      "letter-spacing",
    ]),
  );
  const style = [
    "background-color",
    "border-top-left-radius",
    "padding-top",
    "padding-left",
    "gap",
  ];
  expect(await css(section, style)).toEqual(
    await css(ref.locator("section"), style),
  );
  const actualRow = page.getByRole("button", { name: /sıradaki tekrar yarın/ });
  expect(
    await css(actualRow, ["min-height", "border-top-left-radius"]),
  ).toEqual(
    await css(ref.locator("li a").first(), [
      "min-height",
      "border-top-left-radius",
    ]),
  );
  await expect(actualRow).toHaveAccessibleName(/0 kayıt öğrenildi/);
  const selected = page.getByRole("button", { name: t.byTopic });
  expect(
    await css(selected.getByText(t.byTopic), ["color", "font-size"]),
  ).toEqual(
    await css(ref.getByRole("button", { name: t.byTopic }), [
      "color",
      "font-size",
    ]),
  );
  const before = await actualRow.getAttribute("aria-label");
  await page.screenshot({ path: info.outputPath("notebook.png") });
  await ref.close();
  await page.getByRole("button", { name: t.byMisconception }).click();
  await expect(
    page.getByRole("button", { name: t.byMisconception }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(actualRow).not.toHaveAttribute("aria-label", before!);
  expect(
    await page
      .locator("body")
      .evaluate((body) => body.scrollWidth <= window.innerWidth),
  ).toBe(true);
  await page.getByRole("button", { name: t.early }).click();
  await expect(page.getByRole("heading", { name: t.pass })).toBeVisible();
  await page.getByRole("button", { name: t.continueFree }).click();
  await expect(page).toHaveURL(/\/notebook$/);
  await expect(page.getByText(t.counts(1, 0))).toBeVisible();
});

test("Today's paid review serves a sibling, earns credit and supports early group review", async ({
  page,
}) => {
  const plan = await onboard(page);
  const base = new URL(plan.url()).origin;
  const authorization = await plan.request().headerValue("authorization");
  const fixture = await page.request.post(base + "/fixtures/paid-review", {
    headers: { authorization: authorization! },
  });
  expect(fixture.ok()).toBe(true);
  await page.reload();
  await expect(
    page.getByText(tr.today.review(1), { exact: true }),
  ).toBeVisible();
  const opened = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/v1/practice-sessions" &&
      r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: tr.controls.start, exact: true })
    .click();
  const session: Practice = await (await opened).json();
  expect(session.kind).toBe("review");
  expect(session.question!.id).not.toBe(
    seed.lessons[0]!.check_questions[0]!.question_id,
  );
  expect(session.feedback).toBeNull();
  const item = seed.questions.find((q) => q.id === session.question!.id)!;
  await page
    .getByRole("button", {
      name: new RegExp("^" + item.correct_option + "\\) "),
    })
    .click();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await expect(
    page.getByRole("heading", { name: tr.study.whyRight }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.placement.next }).click();
  await expect(page).toHaveURL(/\/today$/);
  await expect(
    page.getByText(tr.today.reviewMeta + tr.study.done, { exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: tr.nav.notebook, exact: true }).click();
  await expect(page.getByText(t.done)).toBeVisible();
  const row = page.getByRole("button", { name: /sıradaki tekrar 3 gün sonra/ });
  await row.click();
  await expect(
    page.getByRole("progressbar", { name: tr.placement.progress }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.placement.close }).click();
  await expect(page).toHaveURL(/\/notebook$/);
});
