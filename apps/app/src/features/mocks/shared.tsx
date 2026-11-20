import { router } from "expo-router";
import { StyleSheet } from "react-native";
import { Label } from "../../components/Core";
import { ListRow } from "../../components/Study";
import { tr } from "../../i18n/tr";
import { formatDate, formatNumber } from "../../lib/format";
import { colors, radius, space } from "../../theme";
import type { Progress } from "./api";

export const resultRoute = (id: string) => ({
  pathname: "/mock/[attemptId]/result" as const,
  params: { attemptId: id },
});
export function History({ items }: { items: Progress["history"] }) {
  return (
    <>
      <Label accessibilityRole="header" variant="h2">
        {tr.mock.history}
      </Label>
      {items.length === 0 && (
        <Label color={colors.inkMuted}>{tr.mock.noHistory}</Label>
      )}
      {items.map((i) => (
        <ListRow
          key={i.id}
          title={i.title}
          meta={
            formatDate(i.submitted_at) +
            " · " +
            tr.mock.netUnit(formatNumber(i.net))
          }
          onPress={() => router.push(resultRoute(i.id))}
        />
      ))}
    </>
  );
}
export const s = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: space.x8 },
  between: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x8,
  },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.x8 },
  grow: { flex: 1, minWidth: 0 },
  stack: { gap: space.x8 },
  card: { gap: space.x12 },
  examHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.x10,
    paddingHorizontal: space.x12,
    paddingVertical: space.x10,
  },
  timer: {
    backgroundColor: colors.ink,
    borderRadius: radius.field,
    paddingHorizontal: space.x12,
    paddingVertical: space.x6,
    alignItems: "center",
  },
  streak: {
    backgroundColor: colors.butter,
    borderRadius: radius.card,
    padding: space.x16,
    gap: space.x4,
  },
});
