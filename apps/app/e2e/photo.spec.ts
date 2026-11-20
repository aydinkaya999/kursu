import { expect, test } from "@playwright/test";
import example from "../../../content/seed/photo-example.json";
import { tr } from "../src/i18n/tr";
import { css, showReference } from "./reference";

test.use({
  launchOptions: {
    args: [
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
    ],
  },
  permissions: ["camera"],
});

const t = tr.photo;

test("Today opens a private photo, lets its owner report it and links the related lesson", async ({
  page,
  context,
}) => {
  await page.goto("/today");
  await page.getByRole("link", { name: new RegExp(t.tile) }).click();
  await expect(
    page.getByText(t.rights(3)).filter({ visible: true }),
  ).toBeVisible();
  const photo = await page.evaluate((question) => {
    const page = document.createElement("canvas");
    page.width = 480;
    page.height = 240;
    const ink = page.getContext("2d")!;
    ink.fillStyle = "ivory";
    ink.fillRect(0, 0, page.width, page.height);
    ink.fillStyle = "black";
    ink.font = "22px serif";
    let line = "",
      y = 40;
    for (const word of question.split(" ")) {
      if (ink.measureText(line + word).width > 440) {
        ink.fillText(line, 20, y);
        y += 30;
        line = "";
      }
      line += word + " ";
    }
    ink.fillText(line, 20, y);
    return page.toDataURL("image/png").split(",")[1]!;
  }, example.question);
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: t.upload }).click();
  await (
    await chooser
  ).setFiles({
    name: "original.png",
    mimeType: "image/png",
    buffer: Buffer.from(photo, "base64"),
  });
  await expect(page.getByText(t.caution)).toBeVisible();
  await expect(
    page.getByText(t.rights(2)).filter({ visible: true }),
  ).toBeVisible();
  await expect(page.getByRole("img", { name: t.captured })).toBeVisible();
  const url = page.url();
  expect(new URL(url).searchParams.get("id")).toBeTruthy();
  const ref = await context.newPage();
  await showReference(ref, "photo-solve");
  expect(await css(page.getByText(t.caution), ["color", "font-size"])).toEqual(
    await css(ref.getByText(t.caution), ["color", "font-size"]),
  );
  await ref.close();
  await page.screenshot({ path: test.info().outputPath("photo.png") });
  await page.reload();
  await expect(page.getByText(t.caution)).toBeVisible();
  await page.getByRole("button", { name: t.report }).click();
  await page
    .getByRole("textbox", { name: tr.study.reportPrompt })
    .fill("Örnek çözüm geri bildirimi.");
  await page.getByRole("button", { name: tr.study.send }).click();
  await expect(page.getByText(tr.study.thanks)).toBeVisible();
  await page.getByRole("button", { name: tr.study.close }).click();
  await page.getByRole("link", { name: /İlgili mikro ders/ }).click();
  await expect(
    page.getByRole("button", { name: tr.study.nextCard }),
  ).toBeVisible();
  await page.getByRole("button", { name: tr.nav.back }).click();
  await expect(page).toHaveURL(url);
  await page.getByRole("button", { name: t.again }).click();
  await expect(page.getByRole("button", { name: t.upload })).toBeVisible();
  await page.getByRole("button", { name: tr.study.backToday }).click();
  await expect(
    page.getByRole("link", { name: new RegExp(t.tile) }),
  ).toContainText(t.rights(2));
});
test("takes a still frame and releases the camera", async ({ page }) => {
  await page.goto("/photo");
  await page.getByRole("button", { name: t.take }).click();
  const video = page.locator("video");
  await expect(video).toBeVisible();
  await expect(page.getByRole("button", { name: t.take })).toBeEnabled();
  const stream = await video.evaluateHandle(
    (el) => (el as HTMLVideoElement).srcObject as MediaStream,
  );
  await page.getByRole("button", { name: t.take }).click();
  await expect(page.getByText(t.caution)).toBeVisible();
  expect(
    await stream.evaluate((media) =>
      media.getVideoTracks().every((track) => track.readyState === "ended"),
    ),
  ).toBe(true);
  await stream.dispose();
});
