import { client } from "../../lib/api";
import { authorized, requireSuccess } from "../../lib/session";
import type { Answer } from "../placement/api";
import { getLesson } from "../plan/api";
export { getLesson };
export type Lesson = Awaited<ReturnType<typeof getLesson>>;
export type TopicStart = NonNullable<
  Parameters<(typeof client)["/v1/practice-sessions"]["post"]>[0]
>["json"];
export function library() {
  return authorized(async (auth) => {
    const res = await client["/v1/study/lessons"].get(auth);
    requireSuccess(res);
    return res.json();
  });
}
export function startPractice(json: TopicStart) {
  return authorized(async (auth) => {
    const res = await client["/v1/practice-sessions"].post({ ...auth, json });
    requireSuccess(res);
    return res.json();
  });
}
export function getPractice(id: string) {
  return authorized(async (auth) => {
    const res = await client["/v1/practice-sessions/{id}"].get({
      ...auth,
      params: { id },
    });
    requireSuccess(res);
    return res.json();
  });
}
export type Practice = Awaited<ReturnType<typeof getPractice>>;
export type Feedback = NonNullable<Practice["feedback"]>;
export function answerPractice(id: string, json: Answer) {
  return authorized(async (auth) => {
    const res = await client["/v1/practice-sessions/{id}/answers"].post({
      ...auth,
      params: { id },
      json,
    });
    requireSuccess(res);
    return res.json();
  });
}
export function advancePractice(id: string, question_id: string) {
  return authorized(async (auth) => {
    const res = await client["/v1/practice-sessions/{id}/advance"].post({
      ...auth,
      params: { id },
      json: { question_id },
    });
    requireSuccess(res);
    return res.json();
  });
}
export function finishPractice(session: Practice) {
  return authorized(async (auth) => {
    const res = session.lesson_id
      ? await client["/v1/lessons/{id}/complete"].post({
          ...auth,
          params: { id: session.lesson_id },
          json: { session_id: session.id },
        })
      : await client["/v1/practice-sessions/{id}/finish"].post({
          ...auth,
          params: { id: session.id },
        });
    requireSuccess(res);
    return res.json();
  });
}
export function reportQuestion(question_id: string, text: string) {
  return authorized(async (auth) => {
    const res = await client["/v1/content-reports"].post({
      ...auth,
      json: { question_id, text },
    });
    requireSuccess(res);
    return res.json();
  });
}
