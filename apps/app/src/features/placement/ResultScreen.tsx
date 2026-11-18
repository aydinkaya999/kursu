import { useQuery } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { StyleSheet, View } from "react-native";
import {
  Button,
  Card,
  Label,
  PrimaryCard,
  Screen,
} from "../../components/Core";
import { Chip, ProgressBar } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { formatDuration, formatRange } from "../../lib/format";
import { colors, radius, size, space } from "../../theme";
import { placementResult, type Result } from "./api";
import { useMe } from "./queries";
import { StatusScreen } from "./Status";
const t = tr.result;
export default function ResultScreen() {
  const params = useLocalSearchParams<{ id?: string }>(),
    me = useMe();
  const id = params.id ?? me.data?.placement.latest_id;
  const result = useQuery({
    queryKey: ["placement-result", id],
    queryFn: () => placementResult(id!),
    enabled: !!id,
    retry: false,
    networkMode: "always",
  });
  if (!id && me.data)
    return <Redirect href={me.data.profile ? "/today" : "/onboarding"} />;
  if (!result.data)
    return (
      <StatusScreen
        error={result.error ?? me.error}
        retry={() => {
          if (id) void result.refetch();
          else void me.refetch();
        }}
      />
    );
  return (
    <ResultView
      result={result.data}
      onGuest={() => router.replace("/today")}
      onSignup={() => router.push("/auth")}
    />
  );
}
export function ResultView({
  result,
  onGuest,
  onSignup,
}: {
  result: Result;
  onGuest: () => void;
  onSignup: () => void;
}) {
  const preview = result.first_week;
  return (
    <Screen
      contentStyle={s.body}
      footerStyle={s.footer}
      footer={
        <>
          <Button label={t.signup} onPress={onSignup} />
          <Button variant="text" underline label={t.guest} onPress={onGuest} />
        </>
      }
    >
      <Label variant="h1" accessibilityRole="header">
        {t.title}
      </Label>
      <PrimaryCard style={s.hero}>
        <Label variant="meta" weight={700} color={colors.onPrimaryMuted}>
          {t.net}
        </Label>
        <View style={s.score}>
          <Label variant="resultNet" figures color={colors.onPrimary}>
            {formatRange(result.net_low, result.net_high)}
          </Label>
          <Label variant="rowTitle" weight={600} color={colors.onPrimaryMuted}>
            {t.denominator(result.exam_questions)}
          </Label>
        </View>
        <Label variant="resultNote" color={colors.onPrimaryMuted}>
          {t.note(result.total)}
        </Label>
      </PrimaryCard>
      <Card style={s.card}>
        <Label variant="h2" accessibilityRole="header">
          {t.sections}
        </Label>
        <View>
          {result.subtests.map((row) => (
            <View key={row.subtest_id} style={s.row}>
              <View style={s.name}>
                <Label weight={600}>{row.name}</Label>
                {row.priority && (
                  <View style={s.priority}>
                    <Label variant="caption" color={colors.peachInk}>
                      {t.priority}
                    </Label>
                  </View>
                )}
              </View>
              <View style={s.bar}>
                <ProgressBar
                  value={row.correct}
                  max={row.asked}
                  label={row.name}
                  variant="surface"
                />
              </View>
              <Label figures variant="meta" weight={800} style={s.count}>
                {tr.placement.count(row.correct, row.asked)}
              </Label>
            </View>
          ))}
        </View>
      </Card>
      <Card style={s.card}>
        <View style={s.plan}>
          <Label accessibilityRole="header" variant="h2">
            {t.plan}
          </Label>
          <Chip
            tone="butter"
            label={t.daily(formatDuration(preview.daily_minutes))}
          />
        </View>
        <View style={s.lines}>
          {[
            ...preview.topics.map((item) => t.focus(item.subtest, item.topic)),
            t.mock(tr.shared.weekdays[preview.mock_day]),
          ].map((label) => (
            <View key={label} style={s.item}>
              <View style={s.dot} />
              <Label variant="planTopic">{label}</Label>
            </View>
          ))}
        </View>
      </Card>
    </Screen>
  );
}
const s = StyleSheet.create({
  body: { gap: space.x12, paddingTop: space.x22 },
  footer: { paddingBottom: space.x10, gap: 0 },
  hero: { paddingVertical: space.x16, gap: space.x6 },
  score: { flexDirection: "row", alignItems: "baseline", gap: space.x8 },
  card: {
    paddingHorizontal: space.x16,
    paddingVertical: space.x14,
    gap: space.x8,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: size.resultRow,
    gap: space.x10,
  },
  name: {
    flex: 1,
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    gap: space.x6,
  },
  priority: {
    borderRadius: radius.pill,
    backgroundColor: colors.peach,
    paddingHorizontal: space.x7,
    paddingVertical: space.x2,
  },
  bar: { width: size.target },
  count: { minWidth: size.target, textAlign: "right" },
  plan: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: space.x8,
  },
  lines: { gap: space.x4 },
  item: { flexDirection: "row", gap: space.x8 },
  dot: {
    width: space.x6,
    height: space.x6,
    marginTop: space.x7,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
});
