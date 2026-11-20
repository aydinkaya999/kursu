import { render, screen, fireEvent } from "@testing-library/react-native";
import { ExamView } from "../src/features/mocks/Exam";
import { ProgressView } from "../src/features/mocks/Progress";
import type { Attempt, Progress } from "../src/features/mocks/api";
import { tr } from "../src/i18n/tr";
jest.mock("expo-router", () => ({ router: {}, Redirect: () => null }));
const attempt: Attempt = {
  id: "attempt",
  title: "[ÖRNEK] Deneme",
  started_at: "",
  deadline_at: null,
  submitted_at: null,
  mode: "practice",
  position: 1,
  remaining_seconds: null,
  blank: 2,
  questions: [1, 2].map((position) => ({
    position,
    subtest: "Örnek",
    flagged: false,
    selected_option: null,
    question: {
      id: String(position),
      stem: "[ÖRNEK] Soru",
      options: { A: "1", B: "2", C: "3", D: "4", E: "5" },
    },
  })),
};
test("mock permits choice, flag, jump and confirmed submission", async () => {
  const save = jest.fn(),
    move = jest.fn(),
    submit = jest.fn();
  await render(
    <ExamView
      a={attempt}
      seconds={null}
      busy={false}
      onSave={save}
      onMove={move}
      onSubmit={submit}
      retry={jest.fn()}
    />,
  );
  const press = async (name: string | RegExp) =>
    fireEvent.press(screen.getByRole("button", { name }));
  await press("A) 1");
  await press(tr.mock.flag);
  await press(/^2,/);
  expect(save.mock.calls).toEqual([
    [{ selected_option: "A" }],
    [{ flagged: true }],
  ]);
  expect(move).toHaveBeenCalledWith(2);
  await press(tr.mock.finish);
  await press(tr.mock.resume);
  expect(submit).not.toHaveBeenCalled();
  await press(tr.mock.finish);
  await press(tr.mock.end);
  expect(submit).toHaveBeenCalledTimes(1);
});
test("topic map expands and shows the server state and four-week change", async () => {
  const d: Progress = {
    days_to_exam: 30,
    net_range: { low: 21, high: 27 },
    net_change: 2,
    trend: [],
    sections: [
      {
        name: "Örnek",
        mastery_percent: 70,
        topics: [{ name: "Örnek konu", state: "in_progress" }],
      },
    ],
    history: [],
    streak: 2,
    weekly_done: 1,
    weekly_goal: 5,
    detailed: true,
  };
  await render(<ProgressView d={d} />);
  expect(screen.getByText(tr.today.delta("+2"))).toBeTruthy();
  await fireEvent.press(screen.getByRole("button", { name: "Örnek" }));
  expect(screen.getByText("Örnek konu")).toBeTruthy();
});
