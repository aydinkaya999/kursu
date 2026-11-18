import { tr, type Destination } from "../i18n/tr";
import { Label, Screen } from "./Core";
export function DestinationScreen({
  destination,
}: {
  destination: Destination;
}) {
  return (
    <Screen inShell>
      <Label accessibilityRole="header" variant="screenTitle">
        {tr.nav[destination]}
      </Label>
    </Screen>
  );
}
