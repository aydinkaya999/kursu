import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { View } from "react-native";
import {
  Button,
  Card,
  IconButton,
  Label,
  PrimaryCard,
  Screen,
} from "../../components/Core";
import { DataTable } from "../../components/DataTable";
import { Chip, InfoBox } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { formatDate, formatNumber, inflectedNumber } from "../../lib/format";
import { colors } from "../../theme";
import { StudyStatus } from "../study/StudyStatus";
import * as api from "./api";
import { s } from "./shared";
const t = tr.mock;
export default function Result() {
  const { attemptId: id } = useLocalSearchParams<{ attemptId: string }>();
  const q = useQuery({
    queryKey: ["mock-result", id],
    queryFn: () => api.result(id),
    retry: false,
  });
  const cache = useQueryClient();
  useEffect(() => {
    if (q.data)
      for (const key of [
        "mock-history",
        "progress",
        "today",
        "task",
        "notebook",
        "study-library",
      ])
        void cache.invalidateQueries({ queryKey: [key] });
  }, [cache, q.data]);
  const r = q.data,
    back = () => router.dismissTo("/today");
  if (!r)
    return (
      <StudyStatus
        error={q.error}
        retry={() => void q.refetch()}
        onBack={back}
      />
    );
  const review = (filter: string) =>
    router.push({
      pathname: "/mock/[attemptId]/review",
      params: { attemptId: id, filter },
    });
  return (
    <Screen>
      <View style={s.row}>
        <IconButton name="back" label={tr.nav.back} onPress={back} />
        <View style={s.grow}>
          <Label variant="compactTitle" accessibilityRole="header">
            {r.title}
          </Label>
          <Label variant="meta">{formatDate(r.submitted_at)}</Label>
        </View>
      </View>
      <PrimaryCard style={s.card}>
        <Label variant="meta" color={colors.onPrimaryMuted}>
          {t.score}
        </Label>
        <View style={s.row}>
          <Label variant="resultNet" figures color={colors.onPrimary}>
            {formatNumber(r.net)}
          </Label>
          <Label color={colors.onPrimaryMuted}>{t.denominator(r.total)}</Label>
        </View>
        <View style={s.wrap}>
          <Chip tone="mint" label={t.right(r.correct)} />
          <Chip tone="peach" label={t.wrong(r.wrong)} />
          <Chip tone="surface" label={t.blank(r.blank)} />
        </View>
      </PrimaryCard>
      {r.withdrawn > 0 && <Label>{t.withdrawn(r.withdrawn)}</Label>}
      <Card>
        <DataTable
          label={t.summary}
          headers={[t.section, t.score]}
          rows={r.sections.map((i) => [i.name, formatNumber(i.net)])}
        />
      </Card>
      <InfoBox
        icon="info"
        label={
          (r.mode === "timed"
            ? t.used(
                r.duration_minutes,
                inflectedNumber(r.used_minutes, "accusative"),
              )
            : t.elapsed(r.used_minutes)) +
          " " +
          t.focus(r.priorities.join(tr.study.conjunction))
        }
      />
      <Card style={s.stack}>
        <Label variant="h2">{t.distribution}</Label>
        {r.wrong_topics.length ? (
          r.wrong_topics.map((i) => (
            <View key={i.name} style={s.between}>
              <Label>{i.name}</Label>
              <Label>{t.wrong(i.count)}</Label>
            </View>
          ))
        ) : (
          <Label>{t.noneWrong}</Label>
        )}
      </Card>
      {r.wrong > 0 && (
        <Button label={t.review(r.wrong)} onPress={() => review("wrong")} />
      )}
      <Button label={t.all} variant="secondary" onPress={() => review("all")} />
      <Button
        label={t.growth}
        variant="text"
        onPress={() => router.dismissTo("/progress")}
      />
    </Screen>
  );
}
