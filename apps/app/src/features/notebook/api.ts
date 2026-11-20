import { client } from "../../lib/api";
import { authorized, requireSuccess } from "../../lib/session";

export type GroupBy = "topic" | "misconception";
export function notebookGroups(group_by: GroupBy) {
  return authorized(async (auth) => {
    const response = await client["/v1/notebook"].get({
      ...auth,
      query: { group_by },
    });
    requireSuccess(response);
    return response.json();
  });
}
export function notebookSummary() {
  return authorized(async (auth) => {
    const response = await client["/v1/notebook/summary"].get(auth);
    requireSuccess(response);
    return response.json();
  });
}
export type Summary = Awaited<ReturnType<typeof notebookSummary>>;
export type Group = Awaited<ReturnType<typeof notebookGroups>>[number];
