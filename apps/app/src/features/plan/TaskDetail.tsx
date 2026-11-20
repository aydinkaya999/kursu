import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { Screen, Button, Label } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { formatDuration } from "../../lib/format";
import { Status } from "../placement/Status";
import { startPractice } from "../study/api";
import { StudyStatus } from "../study/StudyStatus";
import { getTask, taskAction } from "./api";
import { describe } from "./tasks";

export default function TaskDetail() {
  const { id } = useLocalSearchParams<{ id: string }>(),
    cache = useQueryClient();
  const q = useQuery({
    queryKey: ["task", id],
    queryFn: () => getTask(id),
    enabled: !!id,
    retry: false,
    networkMode: "always",
  });
  const task = q.data;
  const practiceTask =
    !!task &&
    (task.kind === "topic_test" || task.kind === "review") &&
    task.state !== "done";
  const practice = useQuery({
    queryKey: ["task-practice", id],
    queryFn: () =>
      startPractice(
        task?.kind === "review"
          ? { kind: "review", mode: "due", task_id: id }
          : {
              kind: "topic_test",
              content_id: task!.content_id!,
              task_id: id,
            },
      ),
    enabled: practiceTask,
    retry: false,
    networkMode: "always",
    refetchOnWindowFocus: false,
  });
  const back = () => router.dismissTo("/today");
  const complete = useMutation({
    networkMode: "always",
    mutationFn: async () => {
      if (task?.state === "pending") await taskAction(id, "start");
      return taskAction(id, "complete");
    },
    onSuccess: async (value) => {
      cache.setQueryData(["task", id], value);
      await cache.invalidateQueries({ queryKey: ["today"] });
      back();
    },
  });
  if (!task || q.error)
    return (
      <StudyStatus
        error={q.error}
        retry={() => void q.refetch()}
        onBack={back}
      />
    );
  if (task.kind === "lesson" && task.content_id)
    return (
      <Redirect
        href={{
          pathname: "/lessons/[lessonId]",
          params: { lessonId: task.content_id, task: id, from: "today" },
        }}
      />
    );
  if (practiceTask) {
    if (
      practice.error instanceof RequestFailure &&
      practice.error.status === 403
    )
      return (
        <Redirect href={{ pathname: "/paywall", params: { from: "today" } }} />
      );
    if (!practice.data || practice.error)
      return (
        <StudyStatus
          error={practice.error}
          retry={() => void practice.refetch()}
          onBack={back}
        />
      );
    return (
      <Redirect
        href={{
          pathname: "/practice/[sessionId]",
          params: { sessionId: practice.data.id, from: "today" },
        }}
      />
    );
  }
  const summary = describe(task);
  return (
    <Screen
      footer={
        <>
          <Button variant="secondary" label={tr.nav.back} onPress={back} />
          {task.state !== "done" && (
            <Button
              label={tr.today.finish}
              disabled={complete.isPending}
              onPress={() => complete.mutate()}
            />
          )}
        </>
      }
    >
      <Label accessibilityRole="header" variant="h1">
        {summary.title}
      </Label>
      <Label variant="meta">
        {summary.meta} · {formatDuration(task.minutes)}
      </Label>
      {task.state === "done" && <Label>{tr.today.finished}</Label>}
      {complete.error && (
        <Status error={complete.error} retry={() => complete.mutate()} />
      )}
    </Screen>
  );
}
