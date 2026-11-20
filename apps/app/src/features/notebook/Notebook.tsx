import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { SegmentedControl } from "../../components/Choices";
import { Action, IconButton, Label, Screen } from "../../components/Core";
import { Icon } from "../../components/Icon";
import { ListRow } from "../../components/Study";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { colors, radius, size, space } from "../../theme";
import { useConfig } from "../placement/queries";
import { Status } from "../placement/Status";
import { useStartPractice } from "../study/navigation";
import {
  notebookGroups,
  notebookSummary,
  type Group,
  type GroupBy,
  type Summary,
} from "./api";

const t = tr.notebook;
const modes = [
  { value: "topic", label: t.byTopic },
  { value: "misconception", label: t.byMisconception },
] as const;

export function NotebookStatus({
  data,
  busy,
  onStart,
}: {
  data: Summary;
  busy: boolean;
  onStart: () => void;
}) {
  const due = data.due_today > 0;
  return (
    <View role="group" accessibilityLabel={t.status} style={s.status}>
      <View style={s.row}>
        <View style={s.tile}>
          <Icon
            name={due ? "notebook" : "check"}
            size={space.x22}
            color={colors.mintInk}
          />
        </View>
        <View style={s.labels}>
          <Label variant="notebookStatus" color={colors.mintInk}>
            {due ? t.due(data.due_today) : t.done}
          </Label>
          {data.due_tomorrow > 0 && (
            <Label variant="meta" weight={400}>
              {t.tomorrow(data.due_tomorrow)}
            </Label>
          )}
        </View>
      </View>
      {data.open_count > 0 && (
        <Action
          accessibilityLabel={due ? t.start : t.early}
          disabled={busy}
          onPress={onStart}
          style={s.start}
        >
          <Label variant="tileTitle" color={colors.mintInk}>
            {due ? t.start : t.early}
          </Label>
        </Action>
      )}
    </View>
  );
}

export function NotebookRows({
  groups,
  onStart,
}: {
  groups: Group[];
  onStart: (group: Group) => void;
}) {
  return (
    <View style={s.rows}>
      {groups.map((g) => {
        const parts = [g.subtests.join(", ")];
        if (g.next_due_days != null)
          parts.push(t.next(t.when(g.next_due_days)));
        parts.push(t.learned(g.learned_count));
        return (
          <ListRow
            key={g.id}
            title={g.name ?? t.unclassified}
            count={g.open_count}
            meta={parts.join(" · ")}
            onPress={g.open_count ? () => onStart(g) : undefined}
          />
        );
      })}
    </View>
  );
}

export default function Notebook() {
  const [by, setBy] = useState<GroupBy>("topic");
  const config = useConfig();
  const day = config.data?.days_to_exam;
  const summary = useQuery({
    queryKey: ["notebook", "summary", day],
    queryFn: notebookSummary,
    retry: false,
    networkMode: "always",
  });
  const groups = useQuery({
    queryKey: ["notebook", "groups", by, day],
    queryFn: () => notebookGroups(by),
    retry: false,
    networkMode: "always",
  });
  const review = useStartPractice("notebook");
  const data = summary.data;
  function start(group?: Group) {
    if (!data || review.isPending) return;
    const due = group ? group.next_due_days === 0 : data.due_today > 0;
    review.mutate({
      kind: "review",
      mode: due ? "due" : "early",
      ...(group ? { group_by: by, group_id: group.id } : {}),
    });
  }
  return (
    <Screen inShell contentStyle={s.page}>
      <View style={s.row}>
        <IconButton
          name="back"
          label={tr.nav.back}
          onPress={() => router.dismissTo("/today")}
        />
        <View style={s.heading}>
          <Label accessibilityRole="header" variant="notebookTitle">
            {tr.nav.notebook}
          </Label>
          {data && (
            <Label variant="meta" weight={400} color={colors.inkMuted}>
              {t.counts(data.open_count, data.learned_count)}
            </Label>
          )}
        </View>
      </View>
      {!data || summary.error ? (
        <Status error={summary.error} retry={() => void summary.refetch()} />
      ) : data.open_count === 0 && data.learned_count === 0 ? (
        <Label>{t.empty}</Label>
      ) : (
        <>
          <NotebookStatus
            data={data}
            busy={review.isPending}
            onStart={() => start()}
          />
          <SegmentedControl
            label={t.grouping}
            options={modes}
            value={by}
            onChange={setBy}
          />
          {!groups.data || groups.error ? (
            <Status error={groups.error} retry={() => void groups.refetch()} />
          ) : (
            <NotebookRows groups={groups.data} onStart={start} />
          )}
          <View style={s.hint}>
            <Label variant="notebookHint">{t.intervals(data.intervals)}</Label>
          </View>
        </>
      )}
      {review.error instanceof RequestFailure && review.error.status === 409 ? (
        <Label accessibilityRole="alert">{t.unavailable}</Label>
      ) : (
        review.error &&
        !(
          review.error instanceof RequestFailure && review.error.status === 403
        ) && (
          <Status
            error={review.error}
            retry={() => {
              if (review.variables) review.mutate(review.variables);
            }}
          />
        )
      )}
    </Screen>
  );
}
const s = StyleSheet.create({
  page: { paddingVertical: space.x16 },
  row: { flexDirection: "row", alignItems: "center", gap: space.x12 },
  heading: { flex: 1, minWidth: 0 },
  labels: { flex: 1, minWidth: 0, gap: space.x2 },
  status: {
    backgroundColor: colors.mint,
    borderRadius: radius.card,
    paddingVertical: space.x14,
    paddingHorizontal: space.x16,
    gap: space.x12,
  },
  tile: {
    width: size.tileLarge,
    height: size.tileLarge,
    borderRadius: radius.field,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  start: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
  },
  rows: { gap: space.x8, marginTop: -space.x2 },
  hint: {
    borderRadius: radius.option,
    backgroundColor: colors.primaryTint,
    paddingVertical: space.x12,
    paddingHorizontal: space.x14,
    marginTop: -space.x2,
  },
});
