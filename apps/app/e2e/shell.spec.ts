import { expect, test } from "@playwright/test";
import { css, showReference } from "./reference";
import { tr } from "../src/i18n/tr";

test("navigation supports real links, direct entry and browser back", async ({
  page,
  context,
}, info) => {
  await page.goto("/today");
  const menu = page.getByRole("navigation", { name: tr.nav.menu });
  const wide = info.project.name === "desktop";
  await expect(menu.getByRole("link")).toHaveCount(wide ? 5 : 4);
  await expect(menu.getByRole("link", { name: tr.nav.notebook })).toHaveCount(
    wide ? 1 : 0,
  );
  const active = menu.getByRole("link", { name: tr.nav.today });
  await expect(active).toHaveAttribute("aria-current", "page");
  await expect(active).toHaveJSProperty("tagName", "A");
  await expect(menu).toBeInViewport();
  const ref = await context.newPage();
  await showReference(ref, wide ? "web-today" : "today");
  const refNav = ref.getByRole("navigation", { name: tr.nav.menu });
  const refActive = refNav.getByRole("link", { name: tr.nav.today });
  const surface = [
    "background-color",
    "padding-top",
    "padding-left",
    "border-top-left-radius",
  ];
  expect(await css(menu, surface)).toEqual(await css(refNav, surface));
  expect(await css(active, ["min-height"])).toEqual(
    await css(refActive, ["min-height"]),
  );
  if (wide)
    await expect(menu.getByText("Kürsü", { exact: true })).toBeVisible();
  await ref.close();
  await menu.getByRole("link", { name: tr.nav.lessons }).click();
  await expect(page).toHaveURL(/\/lessons$/);
  await expect(
    page.getByRole("heading", { name: tr.nav.lessons }),
  ).toBeVisible();
  await page.reload();
  await expect(
    menu.getByRole("link", { name: tr.nav.lessons }),
  ).toHaveAttribute("aria-current", "page");
  await menu.getByRole("link", { name: tr.nav.mock }).click();
  await expect(page).toHaveURL(/\/mock$/);
  await expect(page.getByRole("heading", { name: tr.nav.mock })).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: tr.nav.lessons }),
  ).toBeVisible();
});
test("switches navigation at 1024 pixels", async ({ page }) => {
  await page.setViewportSize({ width: 1023, height: 800 });
  await page.goto("/progress");
  const nav = page.getByRole("navigation", { name: tr.nav.menu });
  await expect(nav.getByRole("link")).toHaveCount(4);
  expect((await nav.boundingBox())?.width).toBe(560);
  await page.setViewportSize({ width: 1024, height: 800 });
  await expect(nav.getByRole("link")).toHaveCount(5);
  expect((await nav.boundingBox())?.width).toBe(224);
  await nav.getByRole("link", { name: tr.nav.notebook }).click();
  await expect(
    page.getByRole("heading", { name: tr.nav.notebook }),
  ).toBeVisible();
  await expect(
    nav.getByRole("link", { name: tr.nav.notebook }),
  ).toHaveAttribute("aria-current", "page");
});
test("release builds keep the gallery out of links and direct routes", async ({
  page,
}) => {
  const response = await page.goto("/gallery");
  expect(response?.ok()).toBe(true);
  await expect(page).toHaveURL(/\/onboarding$/);
  await expect(
    page.getByRole("heading", { name: tr.onboarding.title }),
  ).toBeVisible();
  await expect(page.getByText(tr.gallery.title, { exact: true })).toHaveCount(
    0,
  );
});
