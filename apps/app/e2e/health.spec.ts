import { expect, test } from "@playwright/test";

import { tr } from "../src/i18n/tr";

test("opening the app displays the live API health result", async ({
  page,
}) => {
  const [response] = await Promise.all([
    page.waitForResponse(
      (reply) =>
        new URL(reply.url()).pathname === "/v1/health" &&
        reply.request().method() === "GET",
    ),
    page.goto("/"),
  ]);

  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ok" });
  await expect(page.locator("html")).toHaveAttribute("lang", "tr");
  await expect(
    page.getByRole("heading", { name: tr.health.title }),
  ).toBeVisible();
  await expect(page.getByText(tr.health.ok, { exact: true })).toBeVisible();
});
