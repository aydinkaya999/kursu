import { StyleSheet, View } from "react-native";
import { tr } from "../i18n/tr";
import { formatNumber } from "../lib/format";
import { colors, line, radius, shadow, size, space, type Tone } from "../theme";
import { Action, Button, Label } from "./Core";
import { Icon, type IconName } from "./Icon";
import { IconTile } from "./Indicators";
type TaskProps = {
  title: string;
  meta: string;
  duration: string;
  icon: IconName;
  tone: Tone;
  state: "pending" | "next" | "done";
  onPress: () => void;
  wide?: boolean;
};
export function TaskRow({
  title,
  meta,
  duration,
  icon,
  tone,
  state,
  onPress,
  wide = false,
}: TaskProps) {
  const next = state === "next",
    done = state === "done";
  const detail = next
    ? meta + " · " + duration
    : done
      ? meta + " · " + tr.controls.complete
      : meta;
  const contents = (
    <View style={styles.row}>
      <IconTile name={done ? "check" : icon} tone={done ? "mint" : tone} />
      <View style={styles.description}>
        <Label variant="rowTitle">{title}</Label>
        <Label variant="meta" color={colors.inkMuted}>
          {detail}
        </Label>
      </View>
      {!next && (
        <Label variant="meta" weight={700} color={colors.inkMuted}>
          {duration}
        </Label>
      )}
    </View>
  );
  if (next)
    return (
      <View style={[styles.task, styles.next, wide && styles.nextWide]}>
        <Action
          accessibilityLabel={title}
          onPress={onPress}
          style={wide && styles.wideTask}
        >
          {contents}
        </Action>
        <Button label={tr.controls.start} compact onPress={onPress} />
      </View>
    );
  return (
    <Action
      accessibilityLabel={[title, detail, duration].join(", ")}
      onPress={onPress}
      style={styles.task}
    >
      {contents}
    </Action>
  );
}
export function ListRow({
  title,
  meta,
  count,
  onPress,
}: {
  title: string;
  meta: string;
  count?: number;
  onPress?: () => void;
}) {
  const Row = onPress ? Action : View;
  return (
    <Row
      accessibilityLabel={[
        title,
        meta,
        count === undefined ? undefined : formatNumber(count),
      ]
        .filter(Boolean)
        .join(", ")}
      onPress={onPress}
      style={styles.list}
    >
      <View style={styles.description}>
        <Label variant="rowTitle">{title}</Label>
        <Label variant="small" weight={400} color={colors.inkMuted}>
          {meta}
        </Label>
      </View>
      {count !== undefined && (
        <View style={styles.count}>
          <Label variant="secondary" color={colors.peachInk} figures>
            {formatNumber(count)}
          </Label>
        </View>
      )}
      {onPress && <Icon name="chevron" size={18} color={colors.inkMuted} />}
    </Row>
  );
}
export type MapQuestion = {
  number: number;
  answered?: boolean;
  flagged?: boolean;
};
export function QuestionMap({
  questions,
  current,
  onSelect,
}: {
  questions: readonly MapQuestion[];
  current: number;
  onSelect: (number: number) => void;
}) {
  const rows = Array.from(
    { length: Math.ceil(questions.length / 5) },
    (_, index) => questions.slice(index * 5, index * 5 + 5),
  );
  return (
    <View role="group" accessibilityLabel={tr.controls.map} style={styles.map}>
      {rows.map((row) => (
        <View key={row[0]!.number} style={styles.mapRow}>
          {row.map((q) => {
            const active = q.number === current;
            const variant = active
              ? "current"
              : q.flagged
                ? "flagged"
                : q.answered
                  ? "answered"
                  : "empty";
            const textColor = {
              current: colors.primaryStrong,
              flagged: colors.butterInk,
              answered: colors.onPrimary,
              empty: colors.inkMuted,
            }[variant];
            const status = [
              q.answered ? tr.controls.answered : tr.controls.empty,
              q.flagged && tr.controls.flagged,
              active && tr.controls.current,
            ]
              .filter(Boolean)
              .join(", ");
            return (
              <Action
                key={q.number}
                onPress={() => onSelect(q.number)}
                accessibilityLabel={formatNumber(q.number) + ", " + status}
                accessibilityState={{ selected: active }}
                aria-current={active ? "step" : undefined}
                style={[styles.mapCell, mapStyles[variant]]}
              >
                {q.flagged && <Icon name="flag" size={12} color={textColor} />}
                <Label
                  variant="tileTitle"
                  weight={variant === "empty" ? 600 : 800}
                  color={textColor}
                  figures
                >
                  {formatNumber(q.number)}
                </Label>
              </Action>
            );
          })}
          {Array.from({ length: 5 - row.length }, (_, i) => (
            <View key={"space" + i} style={styles.spacer} />
          ))}
        </View>
      ))}
    </View>
  );
}
const mapStyles = StyleSheet.create({
  current: {
    backgroundColor: colors.primaryTint,
    borderColor: colors.primary,
    borderWidth: line.selected,
  },
  answered: { backgroundColor: colors.primary },
  flagged: {
    backgroundColor: colors.butter,
    borderColor: colors.butterInk,
    borderWidth: line.selected,
  },
  empty: {
    backgroundColor: colors.surface,
    borderColor: colors.borderControl,
    borderWidth: line.control,
  },
});
const styles = StyleSheet.create({
  task: {
    paddingVertical: space.x12,
    paddingHorizontal: space.x14,
    gap: space.x10,
    backgroundColor: colors.surface,
    borderRadius: radius.task,
    boxShadow: shadow.card,
  },
  next: {
    paddingTop: space.x10,
    paddingHorizontal: space.x12,
    borderWidth: line.selected,
    borderColor: colors.primary,
  },
  nextWide: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  wideTask: { flex: 1 },
  row: { flexDirection: "row", alignItems: "center", gap: space.x12 },
  description: { flex: 1, minWidth: 0, gap: space.x2 },
  list: {
    minHeight: size.cell,
    paddingVertical: space.x8,
    paddingLeft: space.x14,
    paddingRight: space.x10,
    flexDirection: "row",
    alignItems: "center",
    gap: space.x10,
    borderRadius: radius.option,
    backgroundColor: colors.surface,
    boxShadow: shadow.card,
  },
  count: {
    backgroundColor: colors.peach,
    borderRadius: radius.pill,
    minHeight: size.count,
    minWidth: size.count,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: space.x8,
  },
  map: { gap: space.x6 },
  mapRow: { flexDirection: "row", gap: space.x6 },
  mapCell: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: space.x2,
    borderRadius: radius.compact,
  },
  spacer: { flex: 1, minWidth: size.target },
});
