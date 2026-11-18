import { fireEvent, render, screen } from "@testing-library/react-native";
import {
  AnswerRow,
  ChoicePills,
  OptionButton,
  OptionCell,
  SegmentedControl,
} from "../src/components/Choices";
import { Button, IconButton } from "../src/components/Core";
import { ProgressBar, SegmentedProgress } from "../src/components/Indicators";
import { SideNav, TabBar } from "../src/components/Navigation";
import { SelectField } from "../src/components/SelectField";
import { ListRow, QuestionMap, TaskRow } from "../src/components/Study";
import { tr } from "../src/i18n/tr";

const g = tr.gallery;
it("exposes enabled, compact and disabled actions and names icon-only buttons", async () => {
  const press = jest.fn();
  await render(
    <>
      <Button label={g.next} compact onPress={press} />
      <Button label={g.disabled} disabled onPress={press} />
      <IconButton name="cross" label={g.check} onPress={press} />
    </>,
  );
  await fireEvent.press(screen.getByRole("button", { name: g.next }));
  expect(screen.getByRole("button", { name: g.disabled })).toBeDisabled();
  await fireEvent.press(screen.getByRole("button", { name: g.disabled }));
  await fireEvent.press(screen.getByRole("button", { name: g.check }));
  expect(press).toHaveBeenCalledTimes(2);
});
it.each([OptionButton, OptionCell])(
  "announces the selected option and accepts a new answer",
  async (Component) => {
    const press = jest.fn();
    await render(
      <Component letter="A" label={g.option("A")} selected onPress={press} />,
    );
    const control = screen.getByRole("button", {
      selected: true,
      name: "A) " + g.option("A"),
    });
    await fireEvent.press(control);
    expect(press).toHaveBeenCalledTimes(1);
  },
);
it.each([ChoicePills, SegmentedControl])(
  "uses the chosen value for grouped inputs",
  async (Component) => {
    const change = jest.fn();
    await render(
      <Component
        options={[
          { value: "a", label: g.byTopic },
          { value: "b", label: g.byError },
        ]}
        label={g.selectionLabel}
        value="b"
        onChange={change}
      />,
    );
    expect(
      screen.getByRole("button", { selected: true, name: g.byError }),
    ).toBeVisible();
    await fireEvent.press(screen.getByRole("button", { name: g.byTopic }));
    expect(change).toHaveBeenCalledWith("a");
  },
);
it("opens the native field, selects a value and collapses its menu", async () => {
  const change = jest.fn();
  const options = g.fields.map((value) => ({ label: value, value }));
  await render(
    <SelectField
      label={g.field}
      options={options}
      value={g.fields[0]}
      onChange={change}
    />,
  );
  await fireEvent.press(
    screen.getByRole("button", { name: g.field, expanded: false }),
  );
  expect(
    screen.getByRole("button", { name: g.fields[0], selected: true }),
  ).toBeVisible();
  await fireEvent.press(screen.getByRole("button", { name: g.fields[1] }));
  expect(change).toHaveBeenCalledWith(g.fields[1]);
  expect(
    screen.getByRole("button", { name: g.field, expanded: false }),
  ).toBeVisible();
});
it("identifies answers in text and exposes bounded progress", async () => {
  await render(
    <>
      <AnswerRow letter="A" label={g.option("A")} state="correct" />
      <AnswerRow letter="B" label={g.option("B")} state="wrong" />
      <ProgressBar value={130} max={100} label={g.dailyProgress} />
      <SegmentedProgress total={4} done={-1} label={g.lessonProgress} />
    </>,
  );
  expect(screen.getByText(tr.controls.correct)).toBeVisible();
  expect(screen.getByText(tr.controls.wrong)).toBeVisible();
  expect(
    screen.getByRole("progressbar", {
      name: g.dailyProgress,
      value: { now: 100, max: 100 },
    }),
  ).toBeVisible();
  expect(
    screen.getByRole("progressbar", {
      name: g.lessonProgress,
      value: { now: 0, max: 4 },
    }),
  ).toBeVisible();
});
it("supports starting, reopening and selecting study rows", async () => {
  const task = jest.fn(),
    row = jest.fn();
  const props = {
    title: g.topic,
    meta: g.lessonMeta,
    duration: "10 dk",
    icon: "book" as const,
    tone: "primary" as const,
    onPress: task,
  };
  const view = await render(
    <>
      <TaskRow {...props} state="next" />
      <ListRow title={g.listTitle} meta={g.listMeta} count={0} onPress={row} />
    </>,
  );
  await fireEvent.press(
    screen.getByRole("button", { name: tr.controls.start }),
  );
  expect(screen.getByText("0")).toBeVisible();
  await fireEvent.press(
    screen.getByRole("button", { name: new RegExp(g.listTitle) }),
  );
  expect(row).toHaveBeenCalledTimes(1);
  await view.rerender(<TaskRow {...props} state="done" />);
  await fireEvent.press(
    screen.getByRole("button", { name: new RegExp(tr.controls.complete) }),
  );
  expect(task).toHaveBeenCalledTimes(2);
});
it("keeps current, flagged and answered map states accessible together", async () => {
  const select = jest.fn();
  await render(
    <QuestionMap
      current={2}
      questions={[{ number: 1 }, { number: 2, answered: true, flagged: true }]}
      onSelect={select}
    />,
  );
  expect(
    screen.getByRole("button", {
      selected: true,
      name:
        "2, " +
        [tr.controls.answered, tr.controls.flagged, tr.controls.current].join(
          ", ",
        ),
    }),
  ).toBeVisible();
  await fireEvent.press(
    screen.getByRole("button", { name: "1, " + tr.controls.empty }),
  );
  expect(select).toHaveBeenCalledWith(1);
});
it("exposes each navigation destination and the active item", async () => {
  const select = jest.fn();
  const view = await render(<TabBar current="lessons" onSelect={select} />);
  expect(screen.getAllByRole("button")).toHaveLength(4);
  expect(
    screen.getByRole("button", { name: tr.nav.lessons, selected: true }),
  ).toBeVisible();
  await view.rerender(<SideNav current="today" onSelect={select} />);
  expect(screen.getAllByRole("button")).toHaveLength(5);
  await fireEvent.press(screen.getByRole("button", { name: tr.nav.notebook }));
  expect(select).toHaveBeenCalledWith("notebook");
});
