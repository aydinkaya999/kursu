import { useLocalSearchParams } from "expo-router";
import {
  Button,
  Card,
  IconButton,
  Label,
  Screen,
} from "../src/components/Core";
import { leave, origin } from "../src/features/study/navigation";
import { tr } from "../src/i18n/tr";

export default function Paywall() {
  const { from } = useLocalSearchParams<{ from?: string }>();
  const close = () => leave(origin(from ?? "notebook"));
  return (
    <Screen
      footer={<Button label={tr.notebook.continueFree} onPress={close} />}
    >
      <IconButton name="cross" label={tr.study.close} onPress={close} />
      <Label variant="h1" accessibilityRole="header">
        {tr.notebook.pass}
      </Label>
      <Label variant="lead">{tr.notebook.passIntro}</Label>
      <Card>
        <Label variant="h2">{tr.nav.notebook}</Label>
        <Label>{tr.notebook.access}</Label>
      </Card>
    </Screen>
  );
}
