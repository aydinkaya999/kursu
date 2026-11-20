import { client } from "../../lib/api";
import { authorized, checkAccess, requireSuccess } from "../../lib/session";

export function getPhotoQuota() {
  return authorized(async (auth) => {
    const res = await client["/v1/photo-solutions/quota"].get(auth);
    requireSuccess(res);
    return res.json();
  });
}
export function getPhoto(id: string) {
  return authorized(async (auth) => {
    const res = await client["/v1/photo-solutions/{id}"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(res);
    return res.json();
  });
}
export type Solution = Awaited<ReturnType<typeof getPhoto>>;
export type Upload = NonNullable<
  Parameters<(typeof client)["/v1/photo-solutions"]["post"]>[0]
>["json"];

export function solvePhoto(json: Upload) {
  return authorized(async (auth) => {
    const res = await client["/v1/photo-solutions"].post({ ...auth, json });
    await checkAccess(res);
    requireSuccess(res);
    return res.json();
  });
}
export function reportPhoto(photo_solution_id: string, text: string) {
  return authorized(async (auth) => {
    const res = await client["/v1/content-reports"].post({
      ...auth,
      json: { photo_solution_id, text },
    });
    requireSuccess(res);
    return res.json();
  });
}
