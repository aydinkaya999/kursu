import { expect, test } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import { signUp } from "./email-flow";
import { css, showReference } from "./reference";

test("a guest completes onboarding, resumes the same question and receives a first-week plan", async ({
  page,
  context,
}) => {
  test.setTimeout(90000);
  await page.goto("/");
  const t = tr.onboarding;
  await expect(page).toHaveURL(/\/onboarding$/);
  const field = page.getByRole("combobox", { name: t.field }),
    start = page.getByRole("button", { name: t.start });
  await expect(start).toBeDisabled();
  await expect(page.getByRole("button", { name: "60 dk" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(
    page.getByRole("button", { name: t.first, exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await field.selectOption("ingilizce-ogretmenligi");
  await expect(page.getByText(tr.draft.scoreP3)).toBeVisible();
  await page.getByRole("button", { name: "90 dk" }).click();
  await page.getByRole("button", { name: t.repeat, exact: true }).click();
  await page.screenshot({ path: test.info().outputPath("onboarding.png") });
  const ref = await context.newPage();
  await showReference(ref, "onboarding");
  expect(
    await css(start, ["min-height", "border-radius", "background-color"]),
  ).toEqual(
    await css(ref.getByRole("link", { name: t.start }), [
      "min-height",
      "border-radius",
      "background-color",
    ]),
  );
  const begin = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/v1/placement" &&
      r.request().method() === "POST",
  );
  await start.click();
  const first = await (await begin).json();
  expect(Object.keys(first.question).sort()).toEqual(["id", "options", "stem"]);
  await expect(page.getByText(first.question.stem)).toBeVisible();
  await expect(
    page.getByRole("button", { name: tr.placement.next }),
  ).toBeDisabled();
  await showReference(ref, "placement-test");
  const option = page.getByRole("button", { name: /^A\) / });
  const properties = [
    "min-height",
    "border-radius",
    "background-color",
    "border-color",
  ];
  expect(await css(option, properties)).toEqual(
    await css(ref.locator('button[aria-pressed="false"]').first(), properties),
  );
  await option.click();
  await page.getByRole("checkbox", { name: tr.placement.unsure }).click();
  await page.screenshot({ path: test.info().outputPath("placement-test.png") });
  await page.getByRole("button", { name: tr.placement.next }).click();
  const progress = page.getByRole("progressbar", {
    name: tr.placement.progress,
  });
  await expect(progress).toHaveAttribute("aria-valuenow", "2");
  await page.getByRole("button", { name: tr.placement.close }).click();
  await expect(
    page.getByRole("heading", { name: tr.onboarding.title }),
  ).toBeVisible();
  await page.goto("/");
  await expect(page).toHaveURL(/\/today$/);
  const resume = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/v1/placement" &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: tr.draft.resume }).click();
  const second = await (await resume).json();
  expect(second.id).toBe(first.id);
  await page.reload();
  await expect(page.getByText(second.question.stem)).toBeVisible();
  const resultResponse = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === `/v1/placement/${first.id}/result` &&
      r.status() === 200,
  );
  for (let n = 2; n <= 30; n++) {
    await expect(progress).toHaveAttribute("aria-valuenow", String(n));
    await page.getByRole("button", { name: tr.placement.blank }).click();
  }
  await expect(
    page.getByRole("heading", { name: tr.result.title }),
  ).toBeVisible();
  await expect(page.getByText(/^\d+–\d+$/)).toBeVisible();
  await expect(page.getByText(tr.result.priority, { exact: true })).toHaveCount(
    2,
  );
  await expect(page.getByText(tr.result.daily("90 dk"))).toBeVisible();
  const week = (await (await resultResponse).json()).first_week;
  await expect(
    page.getByText(
      tr.result.mock(
        tr.shared.weekdays[week.mock_day as keyof typeof tr.shared.weekdays],
      ),
    ),
  ).toBeVisible();
  await page.screenshot({
    path: test.info().outputPath("placement-result.png"),
  });
  await showReference(ref, "placement-result");
  expect(
    await css(page.getByRole("heading", { name: tr.result.title }), [
      "font-size",
      "line-height",
    ]),
  ).toEqual(
    await css(ref.getByRole("heading", { name: tr.result.title }), [
      "font-size",
      "line-height",
    ]),
  );
  await ref.close();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: tr.result.title }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.result.signup }).click();
  await expect(page).toHaveURL(/\/auth\?.*next=paywall/);
  await signUp(page);
  await expect(
    page.getByRole("heading", { name: tr.notebook.passIntro }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.notebook.continueFree }).click();
  await expect(
    page.getByRole("button", { name: tr.draft.viewResult }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: tr.draft.retake })).toHaveCount(
    0,
  );
});

test("ONB-3 lets a guest explore after choosing a field on one screen", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("combobox", { name: tr.onboarding.field })
    .selectOption("sinif-ogretmenligi");
  await expect(page.getByText(tr.onboarding.scoreP2)).toBeVisible();
  await page.getByRole("button", { name: tr.onboarding.explore }).click();
  await expect(page).toHaveURL(/\/today$/);
  await expect(page.getByText(/^Sınava \d+ gün$/)).toBeVisible();
  await page.goto("/");
  await expect(page).toHaveURL(/\/today$/);
  await page.getByRole("button", { name: tr.onboarding.start }).click();
  await expect(
    page.getByRole("progressbar", { name: tr.placement.progress }),
  ).toHaveAttribute("aria-valuenow", "1");
});
