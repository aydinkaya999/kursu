import { View } from "react-native";
import { Button, Label, Screen } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { space } from "../../theme";
export function Status({
  error,
  retry,
}: {
  error?: unknown;
  retry?: () => void;
}) {
  return (
    <View accessibilityLiveRegion="polite" style={{ gap: space.x8 }}>
      <Label>
        {error
          ? error instanceof TypeError
            ? tr.shared.offline
            : tr.shared.error
          : tr.shared.loading}
      </Label>
      {error && retry ? (
        <Button variant="secondary" label={tr.health.retry} onPress={retry} />
      ) : null}
    </View>
  );
}
export function StatusScreen(props: Parameters<typeof Status>[0]) {
  return (
    <Screen>
      <Status {...props} />
    </Screen>
  );
}
