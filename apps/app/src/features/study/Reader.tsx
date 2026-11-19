import { useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { tr } from "../../i18n/tr";
import { getLesson } from "./api";
import { origin, leave, useStartPractice } from "./navigation";
import { StudyCard } from "./StudyCard";
import { StudyStatus } from "./StudyStatus";
export default function Reader() {
  const { lessonId, task, from, review } = useLocalSearchParams<{
    lessonId: string;
    task?: string;
    from?: string;
    review?: string;
  }>();
  const source = origin(from),
    begin = useStartPractice(source, true);
  const q = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => getLesson(lessonId),
    retry: false,
    networkMode: "always",
  });
  const [index, setIndex] = useState(0);
  function back() {
    if (review && router.canGoBack()) router.back();
    else leave(source);
  }
  if (!q.data || q.error)
    return (
      <StudyStatus
        error={q.error}
        retry={() => void q.refetch()}
        onBack={back}
      />
    );
  const lesson = q.data,
    last = index >= lesson.cards.length - 1;
  const next = () => {
    if (!last) setIndex(index + 1);
    else if (review) back();
    else
      begin.mutate({
        kind: "lesson_check",
        content_id: lesson.id,
        task_id: task,
      });
  };
  return (
    <StudyCard
      lesson={lesson}
      index={Math.min(index, lesson.cards.length - 1)}
      onPrevious={() => setIndex(index - 1)}
      onBack={back}
      onNext={next}
      backLabel={
        review
          ? tr.nav.back
          : source === "today"
            ? tr.study.backToday
            : tr.study.backLessons
      }
      nextLabel={
        last ? (review ? tr.nav.back : tr.study.checks) : tr.study.nextCard
      }
      busy={begin.isPending}
      error={begin.error}
      retry={next}
    />
  );
}
