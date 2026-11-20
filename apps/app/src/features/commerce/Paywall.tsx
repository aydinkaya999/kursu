import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { StyleSheet, View } from "react-native";
import { Button, Card, IconButton, Label, Screen } from "../../components/Core";
import { DataTable } from "../../components/DataTable";
import { Pill } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import {
  formatCurrency,
  formatUntilDate,
  formatNumber,
} from "../../lib/format";
import { colors, space } from "../../theme";
import { useMe } from "../placement/queries";
import { Status } from "../placement/Status";
import { paywall, purchase, type Offer } from "./api";
import { leaveWall, type Destination } from "./navigation";

const t = tr.commerce;
export function PaywallView({
  offer,
  busy,
  onBuy,
  onClose,
  limit,
  error,
}: {
  offer: Offer;
  busy: boolean;
  onBuy: () => void;
  onClose: () => void;
  limit?: boolean;
  error?: unknown;
}) {
  const l = offer.limits;
  const rows = [
    [t.plan, t.first(l.plan_days), t.untilExam],
    [t.questions, t.perDay(l.questions_per_day), t.unlimited],
    [tr.study.micro, t.perDay(l.lessons_per_day), t.unlimited],
    [t.mock, formatNumber(l.mock_exams), t.all],
  ];
  return (
    <Screen
      footer={
        <Label
          variant="caption"
          weight={400}
          style={s.disclaimer}
          color={colors.inkMuted}
        >
          {t.disclaimer}
        </Label>
      }
    >
      <View style={s.header}>
        <Pill label={tr.notebook.pass} tone="butter" />
        <IconButton name="cross" label={tr.study.close} onPress={onClose} />
      </View>
      <Label variant="h1" accessibilityRole="header">
        {tr.notebook.passIntro}
      </Label>
      <Label color={colors.inkMuted}>
        {t.valid(formatUntilDate(offer.results_date))}
      </Label>
      {limit && <Label accessibilityRole="alert">{t.limit}</Label>}
      <Card style={s.table}>
        <DataTable
          label={t.features}
          headers={[t.features, t.free, tr.notebook.pass]}
          rows={rows}
          highlightedColumn={2}
        />
      </Card>
      <View style={s.price}>
        <Label variant="price" figures>
          {formatCurrency(offer.amount_try)}
        </Label>
        <Label variant="meta" color={colors.inkMuted}>
          {t.tax}
        </Label>
      </View>
      <Button
        label={offer.access.active ? t.active : t.buy}
        disabled={busy || !offer.checkout_available || offer.access.active}
        onPress={onBuy}
      />
      <Button
        variant="text"
        label={limit ? t.tomorrow : tr.notebook.continueFree}
        onPress={onClose}
      />
      {!offer.checkout_available && !offer.access.active && (
        <Label>{t.unavailable}</Label>
      )}
      {error ? <Status error={error} retry={onBuy} /> : null}
    </Screen>
  );
}
export default function Paywall() {
  const { from, source, attemptId, counter } =
    useLocalSearchParams<Destination>();
  const intent = { from, source, attemptId, counter };
  const q = useQuery({ queryKey: ["paywall"], queryFn: paywall, retry: false }),
    me = useMe(),
    cache = useQueryClient();
  const close = () => leaveWall(intent);
  const buy = useMutation({
    mutationFn: (o: Offer) => purchase(o),
    onSuccess: async (access) => {
      cache.setQueryData(["entitlement"], access);
      await Promise.all(
        [
          "paywall",
          "entitlement",
          "progress",
          "today",
          "study-library",
          "notebook",
          "task",
          "lesson",
          "mock-history",
        ].map((key) => cache.invalidateQueries({ queryKey: [key] })),
      );
      close();
    },
  });
  if (!q.data || q.error || !me.data || me.error)
    return (
      <Screen>
        <Status
          error={q.error ?? me.error}
          retry={() => {
            void q.refetch();
            void me.refetch();
          }}
        />
        <Button label={tr.notebook.continueFree} onPress={close} />
      </Screen>
    );
  return (
    <PaywallView
      offer={q.data}
      busy={buy.isPending}
      onClose={close}
      error={buy.error}
      limit={
        source === "limit" &&
        (counter === "lessons_per_day" || counter === "questions_per_day")
      }
      onBuy={() => {
        if (me.data.is_guest)
          router.replace({
            pathname: "/auth",
            params: { ...intent, next: "paywall" },
          });
        else buy.mutate(q.data);
      }}
    />
  );
}
const s = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  table: { padding: space.x8 },
  disclaimer: { textAlign: "center" },
  price: { flexDirection: "row", alignItems: "baseline", gap: space.x10 },
});
