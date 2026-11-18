import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Locator, Page } from "@playwright/test";

export async function showReference(page: Page, name: string) {
  const html = readFileSync(
    resolve(__dirname, "../../../docs/design/reference", name + ".html"),
    "utf8",
  );
  // The reference geometry is inline. Avoid the external font service during CI.
  await page.setContent(html.replace(/<link\b[^>]*>/gi, ""));
}
export function css(locator: Locator, properties: string[]) {
  return locator.evaluate(
    (element, props) =>
      props.map((property) =>
        getComputedStyle(element).getPropertyValue(property),
      ),
    properties,
  );
}
