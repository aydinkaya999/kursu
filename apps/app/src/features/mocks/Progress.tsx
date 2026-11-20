import { useQuery } from "@tanstack/react-query";
import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { View } from "react-native";
import Svg, { Polyline } from "react-native-svg";
import {
  Action,
  Card,
  Label,
  PrimaryCard,
  Screen,
} from "../../components/Core";
import { Chip, Pill, ProgressBar } from "../../components/Indicators";
import { Icon } from "../../components/Icon";
import { tr } from "../../i18n/tr";
import {
  formatNumber,
  formatPercent,
  formatRange,
  inflectedNumber,
} from "../../lib/format";
import { colors, space } from "../../theme";
import { Status } from "../placement/Status";
import { progress, type Progress as Data } from "./api";
import { History, s } from "./shared";
const t = tr.progress;
export function ProgressView({ d }: { d: Data }) {
  const [open, setOpen] = useState<string | null>(null);
  const topics = d.sections.flatMap((i) => i.topics);
  return (
    <>
      <PrimaryCard style={s.stack}>
        <Label color={colors.onPrimaryMuted}>{tr.today.net}</Label>
        {d.net_range ? (
          <Label variant="resultNet" color={colors.onPrimary}>
            {formatRange(d.net_range.low, d.net_range.high)}
          </Label>
        ) : (
          <Label color={colors.onPrimary}>{t.noEstimate}</Label>
        )}
        {d.net_change != null && (
          <Label color={colors.onPrimary}>
            {tr.today.delta(
              (d.net_change >= 0 ? "+" : "") + formatNumber(d.net_change),
            )}
          </Label>
        )}
        {d.trend.length >= 2 && (
          <View
            accessible
            accessibilityLabel={t.trend(d.trend.map(formatNumber).join(", "))}
          >
            <Svg
              width="100%"
              height={space.x48}
              viewBox="0 0 100 50"
              preserveAspectRatio="none"
            >
              <Polyline
                points={d.trend
                  .map(
                    (v, i) =>
                      String((100 * i) / (d.trend.length - 1)) +
                      "," +
                      String(48 - v / 2),
                  )
                  .join(" ")}
                fill="none"
                stroke={colors.onPrimary}
                strokeWidth={2}
              />
            </Svg>
          </View>
        )}
      </PrimaryCard>
      {d.sections.length > 0 && (
        <Card style={s.card}>
          <Label variant="h2">{t.mastery}</Label>
          {d.sections.map((i) => (
            <View key={i.name} style={s.row}>
              <Label style={s.grow} variant="meta">
                {i.name}
              </Label>
              <View style={s.grow}>
                <ProgressBar label={i.name} value={i.mastery_percent} />
              </View>
              <Label variant="meta" figures>
                {formatPercent(i.mastery_percent)}
              </Label>
            </View>
          ))}
        </Card>
      )}
      {d.detailed && (
        <>
          <Card style={s.stack}>
            <View style={s.between}>
              <Label variant="h2">{t.map}</Label>
              <Chip label={t.topics(topics.length)} />
            </View>
            <View style={s.wrap}>
              {(["solid", "in_progress", "not_started"] as const).map((k) => (
                <Chip
                  key={k}
                  tone={
                    k === "solid"
                      ? "mint"
                      : k === "in_progress"
                        ? "primary"
                        : "neutral"
                  }
                  label={
                    tr.study.mastery[k] +
                    " " +
                    topics.filter((i) => i.state === k).length
                  }
                />
              ))}
            </View>
            {d.sections.map((i) => (
              <View key={i.name}>
                <Action
                  accessibilityLabel={i.name}
                  accessibilityState={{ expanded: open === i.name }}
                  onPress={() => setOpen(open === i.name ? null : i.name)}
                  style={s.between}
                >
                  <Label>{i.name}</Label>
                  <Icon name="chevron" />
                </Action>
                {open === i.name &&
                  i.topics.map((j) => (
                    <View key={j.name} style={s.between}>
                      <Label variant="meta">{j.name}</Label>
                      <Label variant="caption">
                        {tr.study.mastery[j.state]}
                      </Label>
                    </View>
                  ))}
              </View>
            ))}
          </Card>
          <History items={d.history} />
        </>
      )}
      <View style={s.streak}>
        <View style={s.row}>
          <Icon name="flame" color={colors.butterInk} />
          <Label variant="h2">{t.days(d.streak)}</Label>
        </View>
        <Label>{t.streak}</Label>
        <Label variant="meta">
          {tr.today.weekly(d.weekly_goal, inflectedNumber(d.weekly_done))}
        </Label>
      </View>
    </>
  );
}
export default function Progress() {
  const q = useQuery({
    queryKey: ["progress"],
    queryFn: progress,
    retry: false,
  });
  const refresh = q.refetch;
  useFocusEffect(
    useCallback(() => {
      void refresh();
    }, [refresh]),
  );
  return (
    <Screen inShell>
      <View style={s.between}>
        <Label variant="h1" accessibilityRole="header">
          {tr.nav.progress}
        </Label>
        {q.data && (
          <Pill label={tr.onboarding.countdown(q.data.days_to_exam)} />
        )}
      </View>
      {q.data ? (
        <ProgressView d={q.data} />
      ) : (
        <Status error={q.error} retry={() => void q.refetch()} />
      )}
    </Screen>
  );
}
