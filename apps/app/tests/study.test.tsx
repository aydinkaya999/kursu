import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react-native";
import seed from "../../../content/seed/sample-content.json";
import { Review } from "../src/features/study/Review";
import { StudyCard } from "../src/features/study/StudyCard";
import {
  type Feedback,
  type Lesson,
  reportQuestion,
} from "../src/features/study/api";
import { tr } from "../src/i18n/tr";

jest.mock("../src/features/study/api", () => ({ reportQuestion: jest.fn() }));
const t = tr.study;
const button = (name: string) => screen.getByRole("button", { name });
const law = seed.lessons[0]!;
const lesson: Lesson = {
  ...law,
  is_placeholder: false,
  subtest: seed.subtests[5]!.short_name,
  source: { ...law.source, kind: "law" },
  cards: law.cards.map((c, i) => ({
    ...c,
    kind: c.kind as Lesson["cards"][number]["kind"],
    position: i + 1,
    tip: c.tip ?? null,
  })),
  check_questions: law.check_questions.map((check) => {
    const { id, stem, options } = seed.questions.find(
      (q) => q.id === check.question_id,
    )!;
    return { id, stem, options };
  }),
};
const q = seed.questions.find((row) => row.id === "q.quantitative.0001")!;
const options = ["A", "B", "C", "D", "E"] as const;
const feedback: Feedback = {
  question: { id: q.id, stem: q.stem, options: q.options },
  selected: "A",
  correct: "B",
  is_correct: false,
  rationales: options.map((option) => ({
    option,
    text: q.rationales[option].text,
  })),
  steps: q.solution_steps,
  source: { kind: "lesson", lesson_title: q.source.lesson_title! },
  misconception_count: 3,
  suggest_lesson: true,
  related_lesson_id: lesson.id,
  card_position: null,
};
test("the reader navigates cards and opens and closes the full law text", async () => {
  const next = jest.fn(),
    back = jest.fn();
  await render(
    <StudyCard
      lesson={lesson}
      index={0}
      onNext={next}
      onPrevious={jest.fn()}
      onBack={back}
      backLabel={t.backLessons}
      nextLabel={t.nextCard}
    />,
  );
  expect(button(t.previous)).toBeDisabled();
  expect(screen.getByText(lesson.cards[0]!.title)).toBeVisible();
  await fireEvent.press(button(t.articleText));
  expect(screen.getByText(law.source.quote)).toBeVisible();
  await fireEvent.press(button(t.close));
  expect(screen.queryByText(law.source.quote)).toBeNull();
  await fireEvent.press(button(t.nextCard));
  await fireEvent.press(button(t.backLessons));
  expect(next).toHaveBeenCalledTimes(1);
  expect(back).toHaveBeenCalledTimes(1);
});
async function show(f: Feedback) {
  const next = jest.fn(),
    read = jest.fn(),
    cache = new QueryClient({
      defaultOptions: {
        queries: { gcTime: Infinity },
        mutations: { gcTime: Infinity },
      },
    });
  await render(
    <QueryClientProvider client={cache}>
      <Review
        feedback={f}
        subject={lesson.subtest}
        position={3}
        total={10}
        busy={false}
        onNext={next}
        onLesson={read}
        onBack={jest.fn()}
        retry={jest.fn()}
      />
    </QueryClientProvider>,
  );
  return { next, read, cache };
}
test("feedback opens other rationales, a recommended lesson and a question report", async () => {
  jest.mocked(reportQuestion).mockResolvedValue({ received: true });
  const { next, read, cache } = await show(feedback);
  expect(screen.getByText(t.whyWrong)).toBeVisible();
  expect(screen.getByText(q.rationales.A.text)).toBeVisible();
  expect(screen.getByText(t.misconception(3))).toBeVisible();
  expect(screen.getByText(t.recommended)).toBeVisible();
  const alternate = "B) " + q.rationales.B.text;
  expect(screen.queryByText(alternate)).toBeNull();
  await fireEvent.press(button(t.more));
  expect(screen.getByText(alternate)).toBeVisible();
  await fireEvent.press(button(t.related));
  expect(read).toHaveBeenCalledWith(lesson.id);
  await fireEvent.press(button(t.report));
  expect(button(t.send)).toBeDisabled();
  await fireEvent.changeText(
    screen.getByLabelText(t.reportPrompt),
    "  İşlemi kontrol edin. ",
  );
  await fireEvent.press(button(t.send));
  expect(await screen.findByText(t.thanks)).toBeVisible();
  expect(reportQuestion).toHaveBeenCalledWith(q.id, "İşlemi kontrol edin.");
  await fireEvent.press(button(tr.placement.next));
  expect(next).toHaveBeenCalledTimes(1);
  cache.clear();
});
test("a correct answer shows its own rationale and each imported operation", async () => {
  const { cache } = await show({
    ...feedback,
    selected: "B",
    is_correct: true,
    rationales: [...feedback.rationales].sort(
      (a, b) => Number(b.option === "B") - Number(a.option === "B"),
    ),
    misconception_count: 0,
    suggest_lesson: false,
  });
  expect(screen.getByText(t.whyRight)).toBeVisible();
  expect(screen.getByText(q.rationales.B.text)).toBeVisible();
  expect(screen.queryByText(t.recommended)).toBeNull();
  for (const step of q.solution_steps)
    expect(screen.getByText(step.text)).toBeVisible();
  cache.clear();
});
