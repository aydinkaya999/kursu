import { useQuery } from "@tanstack/react-query";
import { Button, Card, Label } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { getHealth } from "../../lib/api";
import { colors } from "../../theme";
export default function HealthPanel() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => getHealth(signal),
    networkMode: "always",
    retry: false,
  });
  const status = health.isSuccess ? health.data.status : health.status;
  return (
    <Card>
      <Label accessibilityRole="header" variant="h2">
        {tr.health.title}
      </Label>
      <Label accessibilityLiveRegion="polite" color={colors.inkMuted}>
        {tr.health[status]}
      </Label>
      {health.isError && (
        <Button
          variant="secondary"
          label={tr.health.retry}
          onPress={() => void health.refetch()}
        />
      )}
    </Card>
  );
}
