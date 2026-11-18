import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { View } from "react-native";
import { Screen, Card, Button, Label } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { formatDuration } from "../../lib/format";
import { space } from "../../theme";
import { Status, StatusScreen } from "../placement/Status";
import { getTask, getLesson, taskAction } from "./api";
import { describe } from "./tasks";

export default function TaskDetail() {
  const { id } = useLocalSearchParams<{ id?: string }>(),
    cache = useQueryClient();
  const q = useQuery({
      queryKey: ["task", id],
      queryFn: () => getTask(id!),
      enabled: !!id,
      retry: false,
      networkMode: "always",
    }),
    task = q.data;
  const lessonId = task?.kind === "lesson" ? task.content_id : null;
  const lesson = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => getLesson(lessonId!),
    enabled: !!lessonId,
    retry: false,
    networkMode: "always",
  });
  const complete = useMutation({
    networkMode: "always",
    mutationFn: async () => {
      if (task?.state === "pending") await taskAction(id!, "start");
      return taskAction(id!, "complete");
    },
    onSuccess: async (value) => {
      cache.setQueryData(["task", id], value);
      await cache.invalidateQueries({ queryKey: ["today"] });
      router.dismissTo("/today");
    },
  });
  if (!id)
    return (
      <Screen>
        <Button
          label={tr.nav.back}
          onPress={() => router.dismissTo("/today")}
        />
      </Screen>
    );
  if (!task)
    return <StatusScreen error={q.error} retry={() => void q.refetch()} />;
  const summary = describe(task);
  return (
    <Screen
      footer={
        <>
          <Button
            variant="secondary"
            label={tr.nav.back}
            onPress={() => router.dismissTo("/today")}
          />
          {task.state !== "done" && (
            <Button
              label={tr.today.finish}
              disabled={complete.isPending || (!!lessonId && !lesson.data)}
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
      {lessonId && !lesson.data && (
        <Status error={lesson.error} retry={() => void lesson.refetch()} />
      )}
      {lesson.data?.cards.map((card) => (
        <Card key={card.position}>
          <Label variant="h2">{card.title}</Label>
          {card.blocks.map((b, i) => (
            <View key={i} style={{ gap: space.x4 }}>
              <Label weight={700}>{b.heading}</Label>
              <Label>{b.text}</Label>
            </View>
          ))}
          {card.tip && <Label>{card.tip}</Label>}
        </Card>
      ))}
      {task.state === "done" && <Label>{tr.today.finished}</Label>}
      {complete.error && (
        <Status error={complete.error} retry={() => complete.mutate()} />
      )}
    </Screen>
  );
}
