import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { router } from "expo-router";
import Notebook, {
  NotebookRows,
  NotebookStatus,
} from "../src/features/notebook/Notebook";
import {
  notebookGroups,
  notebookSummary,
  type Group,
  type Summary,
} from "../src/features/notebook/api";
import { useStartPractice } from "../src/features/study/navigation";
import { tr } from "../src/i18n/tr";

jest.mock("expo-router", () => ({
  router: { dismissTo: jest.fn() },
  useLocalSearchParams: () => ({ from: "notebook" }),
}));
jest.mock("../src/features/notebook/api", () => ({
  notebookGroups: jest.fn(),
  notebookSummary: jest.fn(),
}));
jest.mock("../src/features/placement/queries", () => ({
  useConfig: () => ({ data: { days_to_exam: 30 } }),
}));
jest.mock("../src/features/study/navigation", () => ({
  ...jest.requireActual("../src/features/study/navigation"),
  useStartPractice: jest.fn(),
}));

const t = tr.notebook;
const summary: Summary = {
  open_count: 2,
  learned_count: 1,
  due_today: 1,
  due_tomorrow: 1,
  intervals: [1, 3, 7, 14, 30],
};
const group: Group = {
  id: "t",
  name: "Örnek konu",
  subtests: ["Sayısal"],
  open_count: 1,
  learned_count: 1,
  next_due_days: 0,
  next_due_on: "2027-05-01",
};
const button = (name: string | RegExp) => screen.getByRole("button", { name });

test("the panel selects due or early review and hides the action once learned", async () => {
  const start = jest.fn();
  const ui = await render(
    <NotebookStatus data={summary} busy={false} onStart={start} />,
  );
  await fireEvent.press(button(t.start));
  await ui.rerender(
    <NotebookStatus
      data={{ ...summary, due_today: 0 }}
      busy={false}
      onStart={start}
    />,
  );
  await fireEvent.press(button(t.early));
  expect(start).toHaveBeenCalledTimes(2);
  await ui.rerender(
    <NotebookStatus
      data={{ ...summary, open_count: 0, due_today: 0, due_tomorrow: 0 }}
      busy={false}
      onStart={start}
    />,
  );
  expect(screen.queryByRole("button")).toBeNull();
});

test("groups include learned counts, due dates and read-only learned rows", async () => {
  const start = jest.fn();
  await render(
    <NotebookRows
      groups={[
        group,
        {
          ...group,
          id: "closed",
          name: null,
          open_count: 0,
          next_due_days: null,
          next_due_on: null,
        },
      ]}
      onStart={start}
    />,
  );
  await fireEvent.press(button(/sıradaki tekrar bugün.*1 kayıt öğrenildi/));
  expect(start).toHaveBeenCalledWith(group);
  expect(screen.getByText(t.unclassified)).toBeVisible();
  expect(screen.getAllByRole("button")).toHaveLength(1);
});

test("the notebook requests the selected grouping and opens its scoped review", async () => {
  const mutate = jest.fn();
  jest
    .mocked(useStartPractice)
    .mockReturnValue({ mutate } as unknown as ReturnType<
      typeof useStartPractice
    >);
  jest.mocked(notebookSummary).mockResolvedValue(summary);
  jest.mocked(notebookGroups).mockImplementation(async (by) => [
    {
      ...group,
      id: by,
      name: by === "topic" ? "Örnek konu" : "Örnek yanılgı",
    },
  ]);
  const cache = new QueryClient({
    defaultOptions: { queries: { gcTime: Infinity } },
  });
  await render(
    <QueryClientProvider client={cache}>
      <Notebook />
    </QueryClientProvider>,
  );
  await screen.findByText(t.counts(2, 1));
  await fireEvent.press(button(t.byMisconception));
  await screen.findByText("Örnek yanılgı");
  await fireEvent.press(button(/Örnek yanılgı/));
  expect(mutate).toHaveBeenCalledWith({
    kind: "review",
    mode: "due",
    group_by: "misconception",
    group_id: "misconception",
  });
  await fireEvent.press(button(tr.nav.back));
  expect(router.dismissTo).toHaveBeenCalledWith("/today");
});
