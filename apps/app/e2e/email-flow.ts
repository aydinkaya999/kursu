import { expect, type Page } from "@playwright/test";
import { randomUUID, createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { tr } from "../src/i18n/tr";

export async function signUp(page: Page) {
  const t = tr.account,
    email = "qa-" + randomUUID() + "@example.org";
  await page.getByRole("button", { name: t.email }).click();
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
}
