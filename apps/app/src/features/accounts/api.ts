import { client } from "../../lib/api";
import {
  authorized,
  platform,
  transport,
  requireSuccess,
  acceptTokens,
  forgetSession,
  notifyAccountChange,
} from "../../lib/session";
export type Provider = "google" | "apple";

export async function startEmail(email: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/auth/email/start"].post({
      ...auth,
      json: { email },
    });
    requireSuccess(r);
  });
}
export async function verifyEmail(email: string, code: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/auth/email/verify"].post({
      ...auth,
      ...transport,
      json: { email, code, platform },
    });
    requireSuccess(r);
    await acceptTokens(await r.json());
    notifyAccountChange();
  });
}
export async function startProvider(provider: Provider) {
  return authorized(async (auth) => {
    const r = await client["/v1/auth/{provider}/start"].post({
      ...auth,
      params: { provider },
      json: { platform },
    });
    requireSuccess(r);
    return r.json();
  });
}
export async function finishProvider(provider: Provider, state: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/auth/{provider}"].post({
      ...auth,
      ...transport,
      params: { provider },
      json: { platform, state },
    });
    requireSuccess(r);
    await acceptTokens(await r.json());
    notifyAccountChange();
  });
}
export async function signOut(remove: boolean) {
  await authorized(async (auth) => {
    const options = { ...auth, ...transport };
    const r = remove
      ? await client["/v1/me"].delete(options)
      : await client["/v1/auth/logout"].post(options);
    requireSuccess(r);
  });
  await forgetSession();
}
export async function getSettings() {
  return authorized(async (auth) => {
    const r = await client["/v1/me/settings"].get(auth);
    requireSuccess(r);
    return r.json();
  });
}
export type Preferences = Awaited<ReturnType<typeof getSettings>>;
export async function saveSettings(json: Preferences) {
  return authorized(async (auth) => {
    const r = await client["/v1/me/settings"].patch({ ...auth, json });
    requireSuccess(r);
    return r.json();
  });
}
