import { readFile, writeFile } from "node:fs/promises";
import { format } from "prettier";
import { tr } from "../apps/app/src/i18n/tr.ts";

const file = new URL("../apps/app/app.json", import.meta.url);
const config = JSON.parse(await readFile(file, "utf8"));
const plugins = config.expo.plugins;
const picker = plugins.find(
  (p) => Array.isArray(p) && p[0] === "expo-image-picker",
);
const options = {
  cameraPermission: tr.photo.cameraPermission,
  photosPermission: tr.photo.photoPermission,
  microphonePermission: false,
};
if (picker) Object.assign(picker[1], options);
else plugins.push(["expo-image-picker", options]);
await writeFile(file, await format(JSON.stringify(config, null, 2), { parser: "json" }));
