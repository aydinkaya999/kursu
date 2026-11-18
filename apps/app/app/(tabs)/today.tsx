import { Link } from "expo-router";
import { Action, Label, Screen } from "../../src/components/Core";
import HealthPanel from "../../src/features/health/HealthPanel";
import { tr } from "../../src/i18n/tr";
import { colors } from "../../src/theme";

import { TodayPlacement } from "../../src/features/placement/TodayPlacement";

export default function Today() {
  return (
    <Screen inShell>
      <Label accessibilityRole="header" variant="h1">
        {tr.nav.today}
      </Label>
      <TodayPlacement />
      <HealthPanel />
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
