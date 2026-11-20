import { client } from "../../lib/api";
import { authorized, checkAccess, requireSuccess } from "../../lib/session";
export function getToday() {
  return authorized(async (auth) => {
    const r = await client["/v1/plan/today"].get(auth);
    await checkAccess(r);
    requireSuccess(r);
    return r.json();
  });
}
export function taskAction(id: string, action: "start" | "complete") {
  return authorized(async (auth) => {
    const o = { ...auth, params: { id } };
    const r =
      action === "start"
        ? await client["/v1/plan/tasks/{id}/start"].post(o)
        : await client["/v1/plan/tasks/{id}/complete"].post(o);
    await checkAccess(r);
    requireSuccess(r);
    return r.json();
  });
}
export function getTask(id: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/plan/tasks/{id}"].get({
      ...auth,
      params: { id },
    });
    await checkAccess(r);
    requireSuccess(r);
    return r.json();
  });
}
export async function getLesson(id: string) {
  return authorized(async (auth) => {
    const r = await client["/v1/lessons/{id}"].get({ ...auth, params: { id } });
    await checkAccess(r);
    requireSuccess(r);
    return r.json();
  });
}
export type Day = Awaited<ReturnType<typeof getToday>>;
export type Task = Day["tasks"][number];
