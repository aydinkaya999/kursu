import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  router,
  useFocusEffect,
  useLocalSearchParams,
} from "expo-router";
import { useCallback, useEffect, useRef, type ReactNode } from "react";
import { Platform, StyleSheet, useWindowDimensions, View } from "react-native";
import {
  Action,
  Button,
  Card,
  Label,
  PrimaryCard,
  Screen,
} from "../../components/Core";
import { Chip, Pill, ProgressBar } from "../../components/Indicators";
import { Icon } from "../../components/Icon";
import { TaskRow } from "../../components/Study";
import { tr } from "../../i18n/tr";
import {
  formatDate,
  formatDuration,
  formatNumber,
  formatPercent,
  formatRange,
  inflectedNumber,
} from "../../lib/format";
import { colors, radius, size, space } from "../../theme";
import { isLimit, limitRoute } from "../commerce/navigation";
import HealthPanel from "../health/HealthPanel";
import { TodayPlacement } from "../placement/TodayPlacement";
import { useConfig, useMe } from "../placement/queries";
import { Status } from "../placement/Status";
import { getToday, taskAction, type Day, type Task } from "./api";
import { describe } from "./tasks";
const t = tr.today;

export function DayView({
  day,
  wide,
  onTask,
  controls,
}: {
  day: Day;
  wide: boolean;
  onTask: (task: Task) => void;
  controls?: ReactNode;
}) {
  const pill = <Pill label={tr.onboarding.countdown(day.days_to_exam)} />;
  const date = (
    <Label variant="meta" weight={600} color={colors.inkMuted}>
      {formatDate(day.plan_date, "weekday")}
    </Label>
  );
  const title = (
    <Label accessibilityRole="header" variant={wide ? "todayWide" : "h1"}>
      {t.title(day.total)}
    </Label>
  );
  const duration = formatDuration(day.remaining_minutes);
  const row = (task: Task) => (
    <TaskRow
      key={task.id}
      {...describe(task)}
      duration={formatDuration(task.minutes)}
      wide={wide}
      state={task.state === "done" ? "done" : task.is_next ? "next" : "pending"}
      onPress={() => onTask(task)}
    />
  );
  return (
    <>
      <View style={wide ? s.wideHead : s.head}>
        {wide ? (
          <>
            <View style={s.head}>
              {date}
              {title}
            </View>
            {pill}
          </>
        ) : (
          <>
            <View style={s.row}>
              {date}
              {pill}
            </View>
            {title}
          </>
        )}
      </View>
      <View style={wide ? s.columns : s.stack}>
        <View style={[s.stack, wide && s.main]}>
          <PrimaryCard style={wide ? s.wideHero : undefined}>
            <View style={s.row}>
              <View style={s.labels}>
                <Label variant="dayCount" color={colors.onPrimary}>
                  {t.summary(day.total, inflectedNumber(day.done))}
                </Label>
                <Label variant="meta" color={colors.onPrimaryMuted}>
                  {day.day_completed
                    ? t.allDone
                    : !day.total
                      ? t.empty
                      : day.done === day.total
                        ? t.allDone
                        : day.done
                          ? t.started(duration)
                          : t.remaining(duration)}
                </Label>
              </View>
              <Label variant="dayPercent" color={colors.onPrimary}>
                {formatPercent(day.percent)}
              </Label>
            </View>
            <ProgressBar
              label={t.progress}
              value={day.percent}
              variant="primary"
            />
          </PrimaryCard>
          {day.tasks.map(row)}
          {day.earlier_completed.length > 0 && (
            <>
              <Label variant="h2">{t.earlier}</Label>
              {day.earlier_completed.map(row)}
            </>
          )}
          <View
            style={s.streak}
            role="group"
            accessibilityLabel={t.streakLabel}
          >
            <View style={s.inline}>
              <Icon name="flame" color={colors.butterInk} />
              <Label weight={700} color={colors.butterInk}>
                {t.streak(day.streak)}
              </Label>
            </View>
            <Label variant="caption" color={colors.butterInk}>
              {t.weekly(day.weekly_goal, inflectedNumber(day.weekly_done))}
            </Label>
          </View>
          {!wide && controls}
        </View>
        {wide && (
          <View style={[s.stack, s.aside]}>
            {!day.net_range && controls}
            {day.net_range && (
              <Card>
                <Label variant="meta">{t.net}</Label>
                <Label variant="display">
                  {formatRange(day.net_range.low, day.net_range.high)}
                </Label>
                {day.net_change !== null && day.net_change !== undefined && (
                  <Chip
                    tone="mint"
                    label={t.delta(
                      (day.net_change > 0 ? "+" : "") +
                        formatNumber(day.net_change),
                    )}
                  />
                )}
              </Card>
            )}
            <Card>
              <Label variant="h2" accessibilityRole="header" aria-level={2}>
                {t.priorities}
              </Label>
              {day.priorities.map((p) => (
                <View key={p.name} style={s.priority}>
                  <Label weight={600} style={s.priorityName}>
                    {p.name}
                  </Label>
                  <View style={s.priorityBar}>
                    <ProgressBar
                      label={p.name}
                      value={p.mastery_percent}
                      variant="surface"
                    />
                  </View>
                  <Label
                    figures
                    variant="meta"
                    weight={800}
                    style={s.priorityValue}
                  >
                    {formatPercent(p.mastery_percent)}
                  </Label>
                </View>
              ))}
            </Card>
            {day.net_range && controls}
          </View>
        )}
      </View>
    </>
  );
}

export default function Today() {
  const { preview } = useLocalSearchParams<{ preview?: string }>();
  const prompted = useRef(false);
  const { width } = useWindowDimensions();
  const wide = Platform.OS === "web" && width >= size.wide;
  const me = useMe(),
    config = useConfig(),
    cache = useQueryClient(),
    enabled = !!me.data?.profile;
  const day = useQuery({
    queryKey: ["today", me.data?.id],
    queryFn: getToday,
    enabled,
    networkMode: "always",
    retry: false,
  });
  const refresh = day.refetch;
  useEffect(() => {
    if (isLimit(day.error) && preview !== "closed" && !prompted.current) {
      prompted.current = true;
      router.push(limitRoute(day.error, "today"));
    }
  }, [day.error, preview]);
  useFocusEffect(
    useCallback(() => {
      if (enabled) void refresh();
    }, [enabled, refresh]),
  );
  useEffect(() => {
    if (enabled && config.dataUpdatedAt) void refresh();
  }, [enabled, refresh, config.dataUpdatedAt]);
  const start = useMutation({
    networkMode: "always",
    mutationFn: (task: Task) =>
      task.state === "done" || task.kind === "review"
        ? Promise.resolve(task)
        : taskAction(task.id, "start"),
    onError: (error) => {
      if (isLimit(error)) router.push(limitRoute(error, "today"));
    },
    onSuccess: (task) => {
      cache.setQueryData(["task", task.id], task);
      router.push({ pathname: "/plan/task", params: { id: task.id } });
    },
  });
  return (
    <Screen inShell contentStyle={wide ? s.pageWide : undefined}>
      {isLimit(day.error) ? (
        <Card>
          <Label>{tr.commerce.planEnded}</Label>
          <Button
            label={tr.commerce.see}
            onPress={() => router.push(limitRoute(day.error, "today"))}
          />
        </Card>
      ) : day.data && enabled ? (
        <DayView
          controls={
            <TodayPlacement
              compact
              showCountdown={false}
              heading={wide && !day.data.net_range ? t.net : undefined}
            />
          }
          day={day.data}
          wide={wide}
          onTask={(task) => {
            if (!start.isPending) start.mutate(task);
          }}
        />
      ) : enabled ? (
        <Status error={day.error} retry={() => void refresh()} />
      ) : (
        <Label accessibilityRole="header" variant="h1">
          {tr.nav.today}
        </Label>
      )}
      {start.error && (
        <Status
          error={start.error}
          retry={() => {
            if (start.variables) start.mutate(start.variables);
          }}
        />
      )}
      {(!day.data || !enabled) && <TodayPlacement />}
      {!wide && (
        <Link href="/notebook" asChild>
          <Action accessibilityRole="link" accessibilityLabel={tr.nav.notebook}>
            <Label variant="link" color={colors.primary}>
              {tr.nav.notebook}
            </Label>
          </Action>
        </Link>
      )}
      <Link href="/settings" asChild>
        <Action
          accessibilityRole="link"
          accessibilityLabel={tr.account.settings}
        >
          <Label variant="link" color={colors.primary}>
            {tr.account.settings}
          </Label>
        </Action>
      </Link>
      {(!enabled || __DEV__) && <HealthPanel />}
      {__DEV__ && (
        <Link href="/gallery" asChild>
          <Action
            accessibilityRole="link"
            accessibilityLabel={tr.gallery.title}
          >
            <Label variant="link" color={colors.primary}>
              {tr.gallery.title}
            </Label>
          </Action>
        </Link>
      )}
    </Screen>
  );
}
const s = StyleSheet.create({
  pageWide: {
    maxWidth: "100%",
    paddingTop: space.x32,
    paddingHorizontal: space.x48,
    paddingBottom: space.x40,
    gap: space.x24,
  },
  stack: { gap: space.x14 },
  head: { gap: space.x10 },
  wideHead: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: space.x16,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: space.x12,
  },
  labels: { flex: 1, gap: space.x2 },
  columns: { flexDirection: "row", gap: space.x24, alignItems: "flex-start" },
  main: { flex: 2, minWidth: 0 },
  aside: { flex: 1, minWidth: 0 },
  wideHero: {
    paddingVertical: space.x20,
    paddingHorizontal: space.x24,
    gap: space.x14,
  },
  streak: {
    padding: space.x12,
    borderRadius: radius.task,
    gap: space.x6,
    backgroundColor: colors.butter,
  },
  inline: { flexDirection: "row", alignItems: "center", gap: space.x8 },
  priority: { flexDirection: "row", alignItems: "center", gap: space.x10 },
  priorityName: { flexBasis: size.priorityName, flexShrink: 1 },
  priorityBar: { flex: 1 },
  priorityValue: { width: space.x40, textAlign: "right" },
});
