import { tr } from "../../i18n/tr";
import type { IconName } from "../../components/Icon";
import type { Tone } from "../../theme";
import type { Task } from "./api";
const t = tr.today;
const icons: Record<Task["kind"], [IconName, Tone]> = {
  review: ["notebook", "peach"],
  lesson: ["book", "primary"],
  topic_test: ["pencil", "butter"],
  mock: ["stopwatch", "aqua"],
};
export function describe(task: Task) {
  const [icon, tone] = icons[task.kind];
  const meta =
    task.kind === "review"
      ? t.reviewMeta
      : task.kind === "lesson"
        ? t.lesson(task.subtest ?? "")
        : task.kind === "topic_test"
          ? t.test(task.subtest ?? "", task.count)
          : t.mock(task.count);
  return {
    title:
      task.kind === "review" ? t.review(task.count) : (task.title ?? t.details),
    meta,
    icon,
    tone,
  };
}
