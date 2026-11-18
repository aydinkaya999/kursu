import { useQuery } from "@tanstack/react-query";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { tr } from "../src/i18n/tr";
import { getHealth } from "../src/lib/api";
import { colors, control, spacing, typography } from "../src/theme";

export default function HealthScreen() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => getHealth(signal),
    networkMode: "always",
    retry: false,
  });
  const status = health.isSuccess ? health.data.status : health.status;

  return (
    <View style={styles.screen}>
      <Text accessibilityRole="header" style={styles.title}>
        {tr.health.title}
      </Text>
      <Text accessibilityLiveRegion="polite" style={styles.status}>
        {tr.health[status]}
      </Text>
      {health.isError && (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={tr.health.retry}
          onPress={() => void health.refetch()}
          style={styles.retry}
        >
          <Text style={styles.retryText}>{tr.health.retry}</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.inset,
    gap: spacing.gap,
    backgroundColor: colors.ground,
  },
  title: { ...typography.title, color: colors.ink },
  status: { ...typography.body, color: colors.inkMuted },
  retry: {
    minHeight: control.minHeight,
    justifyContent: "center",
    paddingHorizontal: spacing.inset,
    borderRadius: control.pillRadius,
    backgroundColor: colors.primaryTint,
  },
  retryText: { ...typography.action, color: colors.primaryStrong },
});
