import { expect, test } from "@playwright/test";
import { tr } from "../src/i18n/tr";
import { css, showReference } from "./reference";
const g = tr.gallery;
test.beforeEach(async ({ page }) => {
  await page.goto("/gallery");
  await expect(page.getByRole("heading", { name: g.title })).toBeVisible({
    timeout: 60000,
  });
});

test("renders the complete development gallery and operates its examples", async ({
  page,
}) => {
  for (const section of [
    g.general,
    g.markers,
    g.indicators,
    g.selection,
    g.study,
    g.data,
    g.navigation,
  ]) {
    await expect(
      page.getByRole("heading", { name: section, exact: true }),
    ).toHaveCount(1);
  }
  const progress = page.getByRole("progressbar", { name: g.dailyProgress });
  await expect(progress).toHaveAttribute("aria-valuenow", "1");
  await page.getByRole("button", { name: g.next, exact: true }).click();
  await expect(progress).toHaveAttribute("aria-valuenow", "2");
  await expect(
    page.getByRole("button", { name: g.disabled }).first(),
  ).toBeDisabled();
  const first = page.getByRole("button", {
    name: "A) " + g.option("A"),
    exact: true,
  });
  await first.focus();
  await first.press("Enter");
  await expect(first).toHaveAttribute("aria-pressed", "true");
  await expect(first).toHaveJSProperty("tagName", "BUTTON");
  const cell = page.getByRole("button", { name: "D) 4", exact: true });
  await cell.click();
  await expect(cell).toHaveAttribute("aria-pressed", "true");
  const group = page.getByRole("button", { name: g.byError });
  await group.click();
  await expect(group).toHaveAttribute("aria-pressed", "true");
  const field = page.getByRole("combobox", { name: g.field });
  await field.selectOption(g.fields[1]);
  await expect(field).toHaveValue(g.fields[1]);
  const map = page.getByRole("group", { name: tr.controls.map });
  const flagged = map.getByRole("button", { name: /^4,/ });
  await flagged.click();
  await expect(flagged).toHaveAttribute("aria-current", "step");
  const table = page.getByRole("table", {
    name: g.tableHeaders[2],
    exact: true,
  });
  await expect(table.getByRole("columnheader")).toHaveCount(3);
  await expect(table.getByRole("rowheader")).toHaveCount(2);
  const sidebar = page.getByRole("navigation", { name: g.webNav });
  await sidebar.getByRole("button", { name: tr.nav.progress }).click();
  await expect(
    page
      .getByRole("navigation", { name: g.phoneNav })
      .getByRole("button", { name: tr.nav.progress }),
  ).toHaveAttribute("aria-current", "page");
  await page
    .getByRole("button", { name: tr.nav.back, exact: true })
    .last()
    .click();
  await expect(page).toHaveURL(/\/today$/);
  await page.getByRole("link", { name: g.title }).click();
  await expect(page.getByRole("heading", { name: g.title })).toBeVisible();
});

test("matches the HTML references for size, shape, colour and typography", async ({
  page,
  context,
}) => {
  const ref = await context.newPage();
  await showReference(ref, "placement-test");
  const option = page.getByRole("button", {
    name: "B) " + g.option("B"),
    exact: true,
  });
  const refOption = ref.locator('[aria-label="Seçenekler"] button').nth(1);
  const box = [
    "min-height",
    "border-top-width",
    "border-top-color",
    "border-top-left-radius",
    "background-color",
  ];
  expect(await css(option, box)).toEqual(await css(refOption, box));
  const plain = page.getByRole("button", {
    name: "A) " + g.option("A"),
    exact: true,
  });
  expect(await css(plain, box)).toEqual(
    await css(ref.locator('[aria-label="Seçenekler"] button').first(), box),
  );
  const iconButton = page.getByRole("button", { name: g.check });
  expect(
    await css(iconButton, [
      "width",
      "height",
      "border-radius",
      "background-color",
    ]),
  ).toEqual(
    await css(ref.getByLabel(g.check), [
      "width",
      "height",
      "border-radius",
      "background-color",
    ]),
  );
  const label = option.getByText(g.option("B"));
  await expect(label).toHaveCSS("font-family", /JakartaExtraBold/);
  expect(await css(label, ["font-size", "color"])).toEqual(
    await css(refOption.locator("span").last(), ["font-size", "color"]),
  );
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          Array.from(document.fonts).filter(
            (face) =>
              face.family.includes("Jakarta") && face.status === "loaded",
          ).length,
      ),
    )
    .toBe(5);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await showReference(ref, "onboarding");
  expect(await css(page.getByRole("combobox", { name: g.field }), box)).toEqual(
    await css(ref.locator("select"), box),
  );
  await showReference(ref, "mock-exam");
  expect(await css(page.getByRole("button", { name: "C) 3" }), box)).toEqual(
    await css(ref.locator('[aria-label="Seçenekler"] button').nth(1), box),
  );
  const flagged = page
    .getByRole("group", { name: tr.controls.map })
    .getByRole("button", { name: /^4,/ });
  expect(await css(flagged, box)).toEqual(
    await css(ref.getByRole("button", { name: /sonra bak/i }).last(), box),
  );
  await showReference(ref, "nationwide-result");
  const firstHeader = page
    .getByRole("table", { name: g.data, exact: true })
    .getByRole("columnheader")
    .first();
  expect(await css(firstHeader, ["font-size", "line-height", "color"])).toEqual(
    await css(ref.locator("thead th").first(), [
      "font-size",
      "line-height",
      "color",
    ]),
  );
  await ref.close();
});

test("keeps enlarged text and the pinned action usable", async ({ page }) => {
  await page.evaluate(() => {
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>("body *"),
    )
      .filter(
        (element) =>
          element.offsetHeight > 0 &&
          Array.from(element.childNodes).some(
            (child) =>
              child.nodeType === Node.TEXT_NODE && child.textContent?.trim(),
          ),
      )
      .map((element) => {
        const style = getComputedStyle(element);
        return {
          element,
          size: parseFloat(style.fontSize),
          line: parseFloat(style.lineHeight),
        };
      });
    for (const { element, size, line } of elements) {
      element.style.fontSize = size * 1.3 + "px";
      if (Number.isFinite(line)) element.style.lineHeight = line * 1.3 + "px";
    }
  });
  const map = page.getByRole("group", { name: tr.controls.map });
  await map.scrollIntoViewIfNeeded();
  const cells = await map.getByRole("button").evaluateAll((elements) =>
    elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return {
        width: rect.width,
        height: rect.height,
        clipped: element.scrollWidth > element.clientWidth + 1,
      };
    }),
  );
  expect(cells).toHaveLength(10);
  expect(
    cells.every(
      (cell) => cell.width >= 44 && cell.height >= 44 && !cell.clipped,
    ),
  ).toBe(true);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  const back = page
    .getByRole("button", { name: tr.nav.back, exact: true })
    .last();
  await expect(back).toBeInViewport();
  await back.click();
  await expect(page.getByRole("heading", { name: tr.nav.today })).toBeVisible();
});
