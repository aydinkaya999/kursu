import { test, expect } from "@playwright/test";
import { randomUUID, createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { tr } from "../src/i18n/tr";

test("a guest signs up, changes account settings and deletes the account", async ({
  page,
}) => {
  const t = tr.account;
  await page.goto("/");
  await page
    .getByRole("combobox", { name: tr.onboarding.field })
    .selectOption("sinif-ogretmenligi");
  await page.getByRole("button", { name: tr.onboarding.explore }).click();
  await page.getByRole("link", { name: t.settings }).click();
  await page.getByRole("button", { name: t.title }).click();
  for (const label of [t.google, t.apple])
    await expect(page.getByRole("button", { name: label })).toBeVisible();
  await page.getByRole("button", { name: t.email }).click();
  const email = "qa-" + randomUUID() + "@example.org";
  await page.getByRole("textbox", { name: t.emailAddress }).fill(email);
  await page.getByRole("button", { name: t.next, exact: true }).click();
  const otp = page.getByRole("textbox", { name: t.code });
  await expect(otp).toBeVisible();
  await otp.fill(
    await readFile(
      resolve(
        __dirname,
        "../test-results/mailbox",
        createHash("sha256").update(email).digest("hex"),
      ),
      "utf8",
    ),
  );
  await page.getByRole("button", { name: t.next, exact: true }).click();
  await expect(page).toHaveURL(/\/today$/);
  await page.reload();
  await page.getByRole("link", { name: t.settings }).click();
  await page.getByRole("button", { name: "30 dk" }).click();
  await page.getByRole("textbox", { name: t.notify }).fill("19:45");
  await page.getByRole("button", { name: t.save }).click();
  await expect(page.getByText(t.saved)).toBeVisible();
  await page.reload();
  await expect(page.getByRole("textbox", { name: t.notify })).toHaveValue(
    "19:45",
  );
  await page.getByRole("button", { name: t.privacy }).click();
  await expect(page.getByText(t.legalPending, { exact: false })).toBeVisible();
  await page.getByRole("button", { name: t.remove }).click();
  await expect(page.getByText(t.confirm)).toBeVisible();
  await page.getByRole("button", { name: t.remove }).click();
  await expect(page).toHaveURL(/\/onboarding$/);
});
