import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import { router } from "expo-router";
import { OnboardingForm } from "../src/features/placement/Onboarding";
import { Question } from "../src/features/placement/TestScreen";
import { ResultView } from "../src/features/placement/ResultScreen";
import {
  saveProfile,
  type Attempt,
  type Guest,
  type Result,
} from "../src/features/placement/api";
import { tr } from "../src/i18n/tr";
import seed from "../../../content/seed/sample-content.json";

jest.mock("expo-router", () => ({
  router: { push: jest.fn(), replace: jest.fn() },
}));
jest.mock("expo-crypto", () => ({
  randomUUID: () => "00000000-0000-4000-8000-000000000001",
}));
jest.mock("../src/features/placement/api", () => ({ saveProfile: jest.fn() }));
const question = seed.questions[0]!;
const safeQuestion = {
  id: question.id,
  stem: question.stem,
  options: question.options,
};
const attempt: Attempt = {
  id: "test",
  kind: "full",
  state: "active",
  position: 1,
  total: 30,
  subtest: seed.subtests[5]!.name,
  question: safeQuestion,
};
const guest: Guest = {
  id: "guest",
  is_guest: true,
  profile: null,
  placement: {
    active_id: null,
    latest_id: null,
    next_retake_on: null,
    can_retake: false,
  },
};
it("ONB-2 and ONB-3 collect the required field and choices in one form", async () => {
  const cache = new QueryClient({
    defaultOptions: {
      queries: { gcTime: Infinity },
      mutations: { gcTime: Infinity },
    },
  });
  const profile = {
    field_id: "ingilizce-ogretmenligi",
    score_type: "P3",
    daily_minutes: 90,
    attempt_kind: "repeat",
  } as const;
  jest.mocked(saveProfile).mockResolvedValue(profile);
  await render(
    <QueryClientProvider client={cache}>
      <OnboardingForm
        guest={guest}
        config={{
          app_name: "Kürsü",
          exam_date: "2027-05-08",
          results_date: "2027-06-11",
          server_now: "2027-01-01T00:00:00Z",
          days_to_exam: 127,
          seconds_to_midnight: 3600,
        }}
        fields={[
          {
            id: profile.field_id,
            name: seed.fields[3]!.name,
            score_type: "P3",
          },
        ]}
      />
    </QueryClientProvider>,
  );
  const button = (name: string) => screen.getByRole("button", { name });
  expect(button(tr.onboarding.start)).toBeDisabled();
  expect(button(tr.onboarding.explore)).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "60 dk", selected: true }),
  ).toBeVisible();
  await fireEvent.press(button(tr.onboarding.field));
  await fireEvent.press(button(seed.fields[3]!.name));
  expect(screen.getByText(tr.draft.scoreP3)).toBeVisible();
  await fireEvent.press(button("90 dk"));
  await fireEvent.press(button(tr.onboarding.repeat));
  await fireEvent.press(button(tr.onboarding.explore));
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/today"));
  expect(saveProfile).toHaveBeenCalledWith({
    field_id: profile.field_id,
    daily_minutes: 90,
    attempt_kind: "repeat",
  });
  expect(cache.getQueryData(["me"])).toEqual({ ...guest, profile });
  cache.clear();
});
it("PLC-3 lets a guest change a selection, mark it unsure and retry with the same answer ID", async () => {
  const send = jest
    .fn()
    .mockRejectedValueOnce(new TypeError())
    .mockResolvedValue(undefined);
  await render(
    <Question
      attempt={attempt}
      question={safeQuestion}
      onSubmit={send}
      onClose={jest.fn()}
    />,
  );
  const next = screen.getByRole("button", { name: tr.placement.next });
  expect(next).toBeDisabled();
  for (const letter of ["A", "B"] as const)
    await fireEvent.press(
      screen.getByRole("button", {
        name: letter + ") " + question.options[letter],
      }),
    );
  await fireEvent.press(
    screen.getByRole("checkbox", { name: tr.placement.unsure }),
  );
  await fireEvent.press(next);
  expect(send.mock.calls[0]![0]).toMatchObject({
    question_id: question.id,
    selected_option: "B",
    not_sure: true,
  });
  await fireEvent.press(
    await screen.findByRole("button", { name: tr.health.retry }),
  );
  expect(send.mock.calls[1]).toEqual(send.mock.calls[0]);
});
it("sends blanks directly and exposes the close action", async () => {
  const send = jest.fn().mockResolvedValue(undefined),
    close = jest.fn();
  await render(
    <Question
      attempt={attempt}
      question={safeQuestion}
      onSubmit={send}
      onClose={close}
    />,
  );
  await fireEvent.press(
    screen.getByRole("button", { name: tr.placement.blank }),
  );
  expect(send).toHaveBeenCalledWith(
    expect.objectContaining({ selected_option: null, not_sure: false }),
  );
  await fireEvent.press(
    screen.getByRole("button", { name: tr.placement.close }),
  );
  expect(close).toHaveBeenCalled();
});
it("renders the supplied range, first-week preview and both result actions", async () => {
  const data: Result = {
    id: "test",
    kind: "short",
    total: 10,
    exam_questions: 80,
    net_low: 27,
    net_high: 33,
    subtests: [],
    first_week: {
      daily_minutes: 30,
      topics: [
        { subtest: seed.subtests[5]!.short_name, topic: seed.topics[0]!.name },
      ],
      mock_day: "sunday",
    },
  };
  const next = jest.fn(),
    signup = jest.fn();
  await render(<ResultView result={data} onGuest={next} onSignup={signup} />);
  expect(screen.getByText("27–33")).toBeVisible();
  expect(screen.getByText(tr.result.note(10))).toBeVisible();
  await fireEvent.press(screen.getByRole("button", { name: tr.result.signup }));
  await fireEvent.press(screen.getByRole("button", { name: tr.result.guest }));
  expect(signup).toHaveBeenCalled();
  expect(next).toHaveBeenCalled();
});
