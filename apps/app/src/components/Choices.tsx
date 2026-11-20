import { StyleSheet, View } from "react-native";
import { colors, line, radius, shadow, size, space } from "../theme";
import { tr } from "../i18n/tr";
import { Action, Label } from "./Core";
import { Icon } from "./Icon";
type OptionProps = {
  letter: string;
  label: string;
  selected: boolean;
  onPress: () => void;
};
export function OptionButton({
  letter,
  label,
  selected,
  onPress,
}: OptionProps) {
  return (
    <Action
      accessibilityLabel={letter + ") " + label}
      accessibilityState={{ selected }}
      aria-pressed={selected}
      onPress={onPress}
      style={[styles.option, selected && styles.selected]}
    >
      <View style={[styles.letter, selected && styles.solid]}>
        <Label
          variant="tileTitle"
          color={selected ? colors.onPrimary : colors.ink}
        >
          {letter}
        </Label>
      </View>
      <Label variant="rowTitle" weight={selected ? 800 : 600}>
        {label}
      </Label>
    </Action>
  );
}
export function OptionCell({ letter, label, selected, onPress }: OptionProps) {
  return (
    <Action
      accessibilityLabel={letter + ") " + label}
      accessibilityState={{ selected }}
      aria-pressed={selected}
      onPress={onPress}
      style={[
        styles.cell,
        selected && styles.selected,
        selected && styles.solid,
      ]}
    >
      <Label
        variant="caption"
        color={selected ? colors.onPrimaryMuted : colors.inkMuted}
      >
        {letter}
      </Label>
      <Label
        variant="secondary"
        color={selected ? colors.onPrimary : colors.ink}
      >
        {label}
      </Label>
    </Action>
  );
}
export function AnswerRow({
  letter,
  label,
  state = "other",
}: {
  letter: string;
  label: string;
  state?: "correct" | "wrong" | "other";
}) {
  const color =
    state === "correct"
      ? colors.mintInk
      : state === "wrong"
        ? colors.dangerInk
        : colors.inkMuted;
  return (
    <View style={[styles.answer, answerColors[state]]}>
      {state !== "other" && (
        <Icon
          name={state === "correct" ? "check" : "cross"}
          size={16}
          color={color}
        />
      )}
      <Label
        variant="meta"
        weight={state === "other" ? 500 : 700}
        color={color}
      >
        {letter + ") " + label}
      </Label>
      {state !== "other" && (
        <Label variant="caption" color={color}>
          {tr.controls[state]}
        </Label>
      )}
    </View>
  );
}
export type Choice<T extends string = string> = { value: T; label: string };
export type ChoiceProps<T extends string = string> = {
  label: string;
  options: readonly Choice<T>[];
  value: T;
  onChange: (value: T) => void;
};
function Group<T extends string>({
  label,
  options,
  value,
  onChange,
  pills,
}: ChoiceProps<T> & { pills: boolean }) {
  return (
    <View
      role="group"
      accessibilityLabel={label}
      style={[styles.group, pills ? styles.choices : styles.segments]}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <Action
            key={option.value}
            accessibilityLabel={option.label}
            accessibilityState={{ selected: active }}
            aria-pressed={active}
            onPress={() => onChange(option.value)}
            style={[
              styles.choice,
              pills ? styles.pill : styles.segment,
              active && (pills ? styles.solid : styles.activeSegment),
            ]}
          >
            <Label
              variant={pills ? "rowTitle" : "tileTitle"}
              weight={active ? 800 : 700}
              color={
                active
                  ? pills
                    ? colors.onPrimary
                    : colors.ink
                  : pills
                    ? colors.ink
                    : colors.inkMuted
              }
              style={styles.center}
            >
              {option.label}
            </Label>
          </Action>
        );
      })}
    </View>
  );
}
export function SegmentedControl<T extends string>(props: ChoiceProps<T>) {
  return <Group {...props} pills={false} />;
}
export function ChoicePills<T extends string>(props: ChoiceProps<T>) {
  return <Group {...props} pills />;
}
const answerColors = StyleSheet.create({
  other: { borderColor: colors.line, backgroundColor: colors.surface },
  correct: {
    borderWidth: line.selected,
    borderColor: colors.success,
    backgroundColor: colors.mint,
    minHeight: size.markedAnswer,
  },
  wrong: {
    borderWidth: line.selected,
    borderColor: colors.danger,
    backgroundColor: colors.dangerTint,
    minHeight: size.markedAnswer,
  },
});
const styles = StyleSheet.create({
  option: {
    flexDirection: "row",
    justifyContent: "flex-start",
    alignItems: "center",
    minHeight: size.option,
    borderWidth: line.control,
    borderColor: colors.borderControl,
    borderRadius: radius.option,
    backgroundColor: colors.surface,
    gap: space.x12,
    paddingHorizontal: space.x14,
    paddingVertical: space.x4,
  },
  selected: {
    borderWidth: line.selected,
    borderColor: colors.primary,
    backgroundColor: colors.primaryTint,
  },
  letter: {
    width: size.letter,
    minHeight: size.letter,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.neutralTint,
    flexShrink: 0,
  },
  cell: {
    flex: 1,
    minHeight: size.cell,
    borderWidth: line.control,
    borderColor: colors.borderControl,
    borderRadius: radius.option,
    backgroundColor: colors.surface,
    alignItems: "center",
    gap: space.x2,
  },
  solid: { backgroundColor: colors.primary, borderColor: colors.primary },
  answer: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: space.x8,
    minHeight: size.answer,
    borderWidth: line.control,
    borderRadius: radius.field,
    paddingVertical: space.x4,
    paddingHorizontal: space.x10,
  },
  group: { flexDirection: "row" },
  choices: { gap: space.x8 },
  segments: {
    padding: space.x4,
    backgroundColor: colors.line,
    borderRadius: radius.pill,
  },
  choice: {
    flex: 1,
    alignItems: "center",
    borderRadius: radius.pill,
    paddingHorizontal: space.x6,
    paddingVertical: space.x4,
  },
  pill: { minHeight: size.choice, backgroundColor: colors.neutralTint },
  segment: { minHeight: size.target },
  activeSegment: { backgroundColor: colors.surface, boxShadow: shadow.segment },
  center: { textAlign: "center" },
});
