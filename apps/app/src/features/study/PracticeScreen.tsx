import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Button, Label, Screen } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { isLimit, limitRoute } from "../commerce/navigation";
import { RequestFailure } from "../../lib/session";
import { Question } from "../placement/TestScreen";
import { Status } from "../placement/Status";
import {
  advancePractice,
  answerPractice,
  finishPractice,
  getPractice,
  getLesson,
  type Practice,
} from "./api";
import { leave, origin } from "./navigation";
import { Review } from "./Review";
import { StudyCard } from "./StudyCard";
import { StudyStatus } from "./StudyStatus";

export default function PracticeScreen() {
  const { sessionId, from } = useLocalSearchParams<{
      sessionId: string;
      from?: string;
    }>(),
    source = origin(from);
  const cache = useQueryClient(),
    key = ["practice", sessionId];
  const q = useQuery({
    queryKey: key,
    queryFn: () => getPractice(sessionId),
    networkMode: "always",
    retry: false,
  });
  const session = q.data,
    f = session?.feedback;
  const [reviewedQuestion, setReviewedQuestion] = useState<string | null>(null);
  const reviewing = !!(
    f &&
    f.question.id === reviewedQuestion &&
    f.card_position &&
    session?.lesson_id
  );
  const lesson = useQuery({
    queryKey: ["lesson", session?.lesson_id],
    queryFn: () => getLesson(session!.lesson_id!),
    enabled: reviewing,
    retry: false,
    networkMode: "always",
  });
  async function close() {
    await Promise.all([
      cache.invalidateQueries({ queryKey: ["today"] }),
      cache.invalidateQueries({ queryKey: ["notebook"] }),
      cache.invalidateQueries({ queryKey: ["task"] }),
      cache.invalidateQueries({ queryKey: ["study-library"] }),
    ]);
    leave(source);
  }
  async function accept(value: Practice) {
    cache.setQueryData(key, value);
    if (value.state === "ready") {
      const finished = await finishPractice(value);
      cache.setQueryData(key, finished);
      await close();
    } else if (value.state === "completed") await close();
  }
  const next = useMutation({
    networkMode: "always",
    mutationFn: async () => {
      if (!session) return;
      if (session.state === "ready") await accept(session);
      else if (f) await accept(await advancePractice(sessionId, f.question.id));
      setReviewedQuestion(null);
    },
    onError: async (error) => {
      if (isLimit(error)) {
        router.replace(limitRoute(error, source));
        return;
      }
      if (error instanceof RequestFailure && [403, 409].includes(error.status))
        await q.refetch();
    },
  });
  const back = () => void close();
  if (isLimit(q.error) || isLimit(lesson.error))
    return <Redirect href={limitRoute(q.error ?? lesson.error, source)} />;
  if (!session || q.error)
    return (
      <StudyStatus
        error={q.error}
        retry={() => void q.refetch()}
        onBack={back}
      />
    );
  if (reviewing && f) {
    if (!lesson.data || lesson.error)
      return (
        <StudyStatus
          error={lesson.error}
          retry={() => void lesson.refetch()}
          onBack={back}
        />
      );
    return (
      <StudyCard
        lesson={lesson.data}
        index={f.card_position! - 1}
        backLabel={tr.nav.back}
        onBack={() => setReviewedQuestion(null)}
        onNext={() => next.mutate()}
        nextLabel={tr.placement.next}
        busy={next.isPending}
        error={next.error}
        retry={() => next.mutate()}
      />
    );
  }
  if (f)
    return (
      <Review
        key={f.question.id}
        feedback={f}
        subject={session.subtest}
        isReview={session.kind === "review"}
        onNotebook={() => {
          void cache.invalidateQueries({ queryKey: ["notebook"] });
          router.push("/notebook");
        }}
        position={session.position}
        total={session.total}
        busy={next.isPending}
        error={next.error}
        retry={() => next.mutate()}
        onNext={() =>
          f.card_position ? setReviewedQuestion(f.question.id) : next.mutate()
        }
        onBack={back}
        onLesson={(lessonId) =>
          router.push({
            pathname: "/lessons/[lessonId]",
            params: { lessonId, from: source, review: "1" },
          })
        }
      />
    );
  if (session.state === "question" && session.question)
    return (
      <Question
        key={session.question.id}
        attempt={session}
        title={tr.study.test(session.subtest)}
        question={session.question}
        onClose={back}
        onSubmit={async (data) => {
          try {
            await accept(await answerPractice(sessionId, data));
          } catch (e) {
            if (isLimit(e)) {
              router.replace(limitRoute(e, source));
              return;
            }
            if (e instanceof RequestFailure && [403, 409].includes(e.status))
              await q.refetch();
            throw e;
          }
        }}
      />
    );
  return (
    <Screen>
      {session.state === "completed" ? (
        <>
          <Label>{tr.study.complete}</Label>
          <Button label={tr.nav.back} onPress={back} />
        </>
      ) : (
        <Button
          label={
            session.lesson_id ? tr.study.finishLesson : tr.study.finishTest
          }
          disabled={next.isPending}
          onPress={() => next.mutate()}
        />
      )}
      {next.error && <Status error={next.error} retry={() => next.mutate()} />}
    </Screen>
  );
}
