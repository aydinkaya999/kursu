import { writeFile } from "node:fs/promises";
import { tr } from "../apps/app/src/i18n/tr.ts";

const destination = new URL(
  "../services/api/app/modules/accounts/email.tr.json",
  import.meta.url,
);
await writeFile(destination, JSON.stringify(tr.emailMessage, null, 2) + "\n");
