import { router } from "expo-router";
import { Button, Label, Screen } from "../src/components/Core";
import { tr } from "../src/i18n/tr";
export default function Auth() {
  return (
    <Screen
      footer={
        <Button
          label={tr.result.guest}
          onPress={() => router.replace("/today")}
        />
      }
    >
      <Label variant="h1" accessibilityRole="header">
        {tr.draft.auth}
      </Label>
      <Label>{tr.draft.authPending}</Label>
    </Screen>
  );
}
