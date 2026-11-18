import { render, screen, fireEvent } from "@testing-library/react-native";
import { DayView } from "../src/features/plan/Today";
import { type Day } from "../src/features/plan/api";
import { tr } from "../src/i18n/tr";
const sample: Day = {
  plan_date: "2027-02-01",
  days_to_exam: 96,
  daily_minutes: 60,
  mock_day: false,
  tasks: [
    {
      id: "review",
      kind: "review",
      content_id: null,
      title: null,
      subtest: null,
      count: 8,
      minutes: 10,
      state: "done",
      is_next: false,
    },
    {
      id: "lesson",
      kind: "lesson",
      content_id: "lesson",
      title: "[ÖRNEK] Test",
      subtest: "Mevzuat",
      count: 0,
      minutes: 5,
      state: "pending",
      is_next: true,
    },
  ],
  earlier_completed: [],
  total: 2,
  done: 1,
  percent: 50,
  day_completed: false,
  remaining_minutes: 5,
  streak: 6,
  weekly_done: 1,
  weekly_goal: 5,
  net_range: { low: 36, high: 40 },
  net_change: 7,
  priorities: [{ name: "Mevzuat", mastery_percent: 30 }],
};
test("Today renders server progress and the selected activity with the weekly goal", async () => {
  const open = jest.fn();
  await render(<DayView day={sample} wide onTask={open} />);
  expect(screen.getByText("2 görevden 1'i tamam")).toBeVisible();
  expect(screen.getByText("Haftalık hedef: 5 günün 1'i")).toBeVisible();
  expect(screen.getByText("36–40")).toBeVisible();
  expect(screen.getByText("Güzel başladın. Kalan süre 5 dk")).toBeVisible();
  await fireEvent.press(
    screen.getByRole("button", { name: tr.controls.start }),
  );
  expect(open).toHaveBeenCalledWith(sample.tasks[1]);
});
test("a completed phone plan displays weekly credit and neutral completion copy", async () => {
  await render(
    <DayView
      wide={false}
      day={{
        ...sample,
        done: 2,
        percent: 100,
        remaining_minutes: 0,
        tasks: sample.tasks.map((t) => ({
          ...t,
          state: "done",
          is_next: false,
        })),
      }}
      onTask={jest.fn()}
    />,
  );
  expect(screen.getByText(tr.today.allDone)).toBeVisible();
  expect(screen.queryByText(tr.controls.start)).toBeNull();
});
