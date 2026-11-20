import { client } from "../../lib/api";
import { authorized, checkAccess, requireSuccess } from "../../lib/session";
export type Mode = "timed" | "practice";
type Save = NonNullable<
  Parameters<
    (typeof client)["/v1/mock-attempts/{id}/answers/{question_id}"]["put"]
  >[0]
>["json"];
export function catalogue() {
  return authorized(async (auth) => {
    const response = await client["/v1/mocks"].get({ ...auth });
    requireSuccess(response);
    return response.json();
  });
}
export function history() {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-history"].get({ ...auth });
    requireSuccess(response);
    return response.json();
  });
}
export function progress() {
  return authorized(async (auth) => {
    const response = await client["/v1/progress"].get({ ...auth });
    requireSuccess(response);
    return response.json();
  });
}
export function start(id: string, json: { mode: Mode }) {
  return authorized(async (auth) => {
    const response = await client["/v1/mocks/{id}/attempts"].post({
      ...auth,
      params: { id },
      json,
    });
    await checkAccess(response);
    requireSuccess(response);
    return response.json();
  });
}
export function attempt(id: string) {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-attempts/{id}"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(response);
    return response.json();
  });
}
export function save(id: string, question_id: string, json: Save) {
  return authorized(async (auth) => {
    const response = await client[
      "/v1/mock-attempts/{id}/answers/{question_id}"
    ].put({ ...auth, params: { id, question_id }, json });
    requireSuccess(response);
    return response.json();
  });
}
export function move(id: string, json: { position: number }) {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-attempts/{id}/position"].put({
      ...auth,
      params: { id },
      json,
    });
    requireSuccess(response);
    return response.json();
  });
}
export function submit(id: string) {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-attempts/{id}/submit"].post({
      ...auth,
      params: { id },
    });
    requireSuccess(response);
    return response.json();
  });
}
export function result(id: string) {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-attempts/{id}/result"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(response);
    return response.json();
  });
}
export function review(id: string) {
  return authorized(async (auth) => {
    const response = await client["/v1/mock-attempts/{id}/review"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(response);
    return response.json();
  });
}
export type Attempt = Awaited<ReturnType<typeof attempt>>;
export type Letter = keyof NonNullable<
  Attempt["questions"][number]["question"]
>["options"];
export type MockResult = Awaited<ReturnType<typeof result>>;
export type Progress = Awaited<ReturnType<typeof progress>>;
