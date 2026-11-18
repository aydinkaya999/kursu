import { router } from "expo-router";
import { useState, type ReactNode } from "react";
import { StyleSheet, View } from "react-native";
import {
  AnswerRow,
  ChoicePills,
  OptionButton,
  OptionCell,
  SegmentedControl,
} from "../../components/Choices";
import {
  Button,
  Card,
  IconButton,
  Label,
  PrimaryCard,
  Screen,
} from "../../components/Core";
import { DataTable } from "../../components/DataTable";
import { type IconName } from "../../components/Icon";
import {
  Chip,
  IconTile,
  InfoBox,
  Pill,
  ProgressBar,
  SegmentedProgress,
} from "../../components/Indicators";
import { SideNav, TabBar } from "../../components/Navigation";
import { SelectField } from "../../components/SelectField";
import { ListRow, QuestionMap, TaskRow } from "../../components/Study";
import { tr, type Destination } from "../../i18n/tr";
import {
  formatDuration,
  formatNumber,
  formatPercent,
  inflectedNumber,
} from "../../lib/format";
import { colors, space, type Tone } from "../../theme";

const g = tr.gallery;
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.section}>
      <Label variant="screenTitle" accessibilityRole="header">
        {title}
      </Label>
      {children}
    </View>
  );
}
function CardSamples() {
  const [step, setStep] = useState(1);
  const advance = () => setStep((n) => (n + 1) % 5);
  return (
    <Section title={g.general}>
      <PrimaryCard>
        <Label variant="h2" color={colors.onPrimaryMuted}>
          {g.dailyProgress}
        </Label>
        <Label variant="display" color={colors.onPrimary} figures>
          {formatPercent(step * 25)}
        </Label>
        <ProgressBar
          label={g.dailyProgress}
          variant="primary"
          max={4}
          value={step}
        />
        <Label variant="body" color={colors.onPrimary}>
          {g.tasksDone(inflectedNumber(step))}
        </Label>
      </PrimaryCard>
      <Card>
        <Label variant="h2" accessibilityRole="header">
          {g.surface}
        </Label>
        <Button label={g.next} onPress={advance} />
        <Button
          label={g.previous}
          variant="secondary"
          onPress={() => setStep((n) => (n + 4) % 5)}
        />
        <Button
          label={g.text}
          variant="text"
          onPress={() => router.navigate("/today")}
        />
        <Button
          label={g.quiet}
          variant="quiet"
          onPress={() => router.navigate("/today")}
        />
        <Button label={g.disabled} disabled onPress={advance} />
        <View style={styles.wrap}>
          <IconButton
            name="back"
            label={tr.nav.back}
            onPress={() => router.navigate("/today")}
          />
          <IconButton
            name="cross"
            label={g.check}
            onPress={() => router.navigate("/today")}
          />
          <IconButton
            name="chevron"
            label={g.disabled}
            disabled
            onPress={advance}
          />
        </View>
      </Card>
    </Section>
  );
}
const toneLabels: Record<Tone, string> = {
  primary: g.lesson,
  neutral: g.section,
  surface: g.section,
  mint: g.done,
  butter: g.time,
  peach: g.mistakes,
  rose: g.iconNames.medal,
  aqua: g.reference,
  danger: tr.controls.wrong,
};
const tones = Object.keys(toneLabels) as Tone[];
const iconNames = Object.keys(g.iconNames) as IconName[];
const iconTones: Partial<Record<IconName, Tone>> = {
  check: "mint",
  cross: "danger",
  notebook: "peach",
  pencil: "butter",
  camera: "rose",
  flame: "butter",
  flag: "butter",
  info: "aqua",
  lightbulb: "butter",
  medal: "rose",
  trophy: "aqua",
};
function Markers() {
  return (
    <Section title={g.markers}>
      <Card>
        <View style={styles.wrap}>
          {tones.map((tone) => (
            <Pill key={tone} tone={tone} label={toneLabels[tone]} />
          ))}
        </View>
        <View style={styles.wrap}>
          {tones.map((tone) => (
            <Chip key={tone} tone={tone} label={toneLabels[tone]} />
          ))}
        </View>
      </Card>
      <Card>
        <Label variant="h2">{g.icons}</Label>
        <View style={styles.wrap}>
          {iconNames.map((name) => (
            <View key={name} style={styles.iconSample}>
              <IconTile
                name={name}
                scale={
                  name === "book"
                    ? "large"
                    : name === "flag"
                      ? "small"
                      : "medium"
                }
                tone={iconTones[name] ?? "primary"}
              />
              <Label variant="caption" color={colors.inkMuted}>
                {g.iconNames[name]}
              </Label>
            </View>
          ))}
        </View>
      </Card>
      <InfoBox label={g.reference} icon="info" tone="aqua" />
      <InfoBox label={g.done} tone="mint" />
    </Section>
  );
}
function ProgressSamples() {
  return (
    <Section title={g.indicators}>
      <ProgressBar label={g.questionProgress} value={0} />
      <Card>
        <ProgressBar label={g.lessonProgress} value={50} variant="surface" />
        <ProgressBar label={g.mockProgress} value={100} variant="mock" />
      </Card>
      {[0, 2, 4].map((done) => (
        <SegmentedProgress
          key={done}
          label={g.lessonProgress}
          total={4}
          done={done}
        />
      ))}
    </Section>
  );
}
const fieldOptions = g.fields.map((value) => ({ value, label: value }));
const durationOptions = ([30, 60, 90] as const).map((value) => ({
  value: String(value),
  label: formatDuration(value),
}));
const groups = [
  { value: "topic", label: g.byTopic },
  { value: "error", label: g.byError },
];
function SelectionSamples() {
  const [field, setField] = useState<string>(g.fields[0]);
  const [minutes, setMinutes] = useState("60");
  const [group, setGroup] = useState("topic");
  const [long, setLong] = useState<string>("B");
  const [compact, setCompact] = useState<string>("C");
  return (
    <Section title={g.selection}>
      <Card>
        <SelectField
          label={g.field}
          options={fieldOptions}
          value={field}
          onChange={setField}
        />
        <Label variant="tileTitle">{g.minutes}</Label>
        <ChoicePills
          label={g.minutes}
          options={durationOptions}
          value={minutes}
          onChange={setMinutes}
        />
      </Card>
      <SegmentedControl
        label={g.selectionLabel}
        options={groups}
        value={group}
        onChange={setGroup}
      />
      <Label variant="h2">{g.options}</Label>
      <View role="group" accessibilityLabel={g.options} style={styles.stack}>
        {g.letters.map((letter) => (
          <OptionButton
            key={letter}
            letter={letter}
            label={g.option(letter)}
            selected={long === letter}
            onPress={() => setLong(letter)}
          />
        ))}
      </View>
      <Label variant="h2">{g.compact}</Label>
      <View role="group" accessibilityLabel={g.compact} style={styles.cells}>
        {g.letters.map((letter, index) => (
          <OptionCell
            key={letter}
            letter={letter}
            label={formatNumber(index + 1)}
            selected={compact === letter}
            onPress={() => setCompact(letter)}
          />
        ))}
      </View>
      <Label variant="h2">{g.feedback}</Label>
      {g.letters.map((letter, index) => (
        <AnswerRow
          key={letter}
          letter={letter}
          label={g.option(letter)}
          state={index === 0 ? "wrong" : index === 2 ? "correct" : "other"}
        />
      ))}
    </Section>
  );
}
const sampleTasks = [
  {
    title: g.rowLabel,
    meta: g.rowMeta,
    icon: "notebook",
    tone: "mint",
    minutes: 5,
  },
  {
    title: g.topic,
    meta: g.lessonMeta,
    icon: "book",
    tone: "primary",
    minutes: 10,
  },
  {
    title: g.taskTitle,
    meta: g.taskMeta,
    icon: "pencil",
    tone: "butter",
    minutes: 15,
  },
] as const;
const questions = Array.from({ length: 10 }, (_, i) => ({
  number: i + 1,
  answered: i < 2,
  flagged: i === 3,
}));
function StudySamples() {
  const [next, setNext] = useState(1);
  const [current, setCurrent] = useState(3);
  const [expanded, setExpanded] = useState<string | null>(null);
  const toggle = (key: string) =>
    setExpanded((value) => (value === key ? null : key));
  return (
    <Section title={g.study}>
      {sampleTasks.map((task, index) => (
        <TaskRow
          key={task.title}
          {...task}
          duration={formatDuration(task.minutes)}
          state={index === next ? "next" : index < next ? "done" : "pending"}
          onPress={() =>
            setNext(index === next ? (next + 1) % sampleTasks.length : index)
          }
        />
      ))}
      <ListRow
        title={g.listTitle}
        meta={g.listMeta}
        count={3}
        onPress={() => toggle("topic")}
      />
      {expanded === "topic" && <InfoBox label={g.rowMeta} icon="notebook" />}
      <ListRow
        title={g.rowLabel}
        meta={g.rowMeta}
        onPress={() => toggle("review")}
      />
      {expanded === "review" && <InfoBox label={g.listTitle} icon="book" />}
      <Card>
        <Label variant="h2">{g.testMap}</Label>
        <QuestionMap
          questions={questions}
          current={current}
          onSelect={setCurrent}
        />
      </Card>
    </Section>
  );
}
const rows = [
  [g.subjects[0], formatNumber(8), formatNumber(7.75)],
  [g.subjects[1], formatNumber(6), formatNumber(5.5)],
];
function NavigationSamples() {
  const [current, setCurrent] = useState<Destination>("today");
  return (
    <Section title={g.navigation}>
      <TabBar label={g.phoneNav} current={current} onSelect={setCurrent} />
      <SideNav label={g.webNav} current={current} onSelect={setCurrent} />
    </Section>
  );
}
export default function Gallery() {
  return (
    <Screen
      footer={
        <Button
          label={tr.nav.back}
          variant="secondary"
          onPress={() => router.navigate("/today")}
        />
      }
    >
      <Label variant="h1" accessibilityRole="header">
        {g.title}
      </Label>
      <CardSamples />
      <Markers />
      <ProgressSamples />
      <SelectionSamples />
      <StudySamples />
      <Section title={g.data}>
        <Card>
          <DataTable label={g.data} headers={g.tableHeaders} rows={rows} />
        </Card>
        <Card>
          <DataTable
            label={g.tableHeaders[2]}
            headers={g.tableHeaders}
            rows={rows}
            highlightedColumn={2}
          />
        </Card>
      </Section>
      <NavigationSamples />
    </Screen>
  );
}
const styles = StyleSheet.create({
  section: { gap: space.x12, marginBottom: space.x12 },
  wrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: space.x8,
    alignItems: "center",
  },
  iconSample: { alignItems: "center", gap: space.x4, padding: space.x4 },
  stack: { gap: space.x8 },
  cells: { flexDirection: "row", gap: space.x6 },
});
