import { client } from "../../lib/api";
import { authorized, requireSuccess } from "../../lib/session";

export async function getConfig() {
  const r = await client["/v1/config"].get();
  requireSuccess(r);
  return r.json();
}
export async function listFields() {
  const r = await client["/v1/fields"].get();
  requireSuccess(r);
  return r.json();
}
export function getMe() {
  return authorized(async (auth) => {
    const r = await client["/v1/me"].get(auth);
    requireSuccess(r);
    return r.json();
  });
}
type ProfileInput = NonNullable<
  Parameters<(typeof client)["/v1/me/profile"]["patch"]>[0]
>["json"];
export function saveProfile(json: ProfileInput) {
  return authorized(async (auth) => {
    const r = await client["/v1/me/profile"].patch({ ...auth, json });
    requireSuccess(r);
    return r.json();
  });
}
export function startPlacement(kind: "full" | "short") {
  return authorized(async (auth) => {
    const r = await client["/v1/placement"].post({ ...auth, json: { kind } });
    requireSuccess(r);
    return r.json();
  });
}
export type Answer = NonNullable<
  Parameters<(typeof client)["/v1/placement/{id}/answers"]["post"]>[0]
>["json"];
export function answerPlacement(id: string, json: Answer) {
  return authorized(async (auth) => {
    const r = await client["/v1/placement/{id}/answers"].post({
      ...auth,
      params: { id },
      json,
    });
    requireSuccess(r);
    return r.json();
  });
}
export function placementResult(id: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/placement/{id}/result"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(r);
    return r.json();
  });
}
export type Guest = Awaited<ReturnType<typeof getMe>>;
export type Attempt = Awaited<ReturnType<typeof startPlacement>>;
export type Result = Awaited<ReturnType<typeof placementResult>>;
