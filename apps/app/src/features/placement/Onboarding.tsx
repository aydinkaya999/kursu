import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Button, Card, Label, Screen } from "../../components/Core";
import { ChoicePills } from "../../components/Choices";
import { SelectField } from "../../components/SelectField";
import { Chip } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { formatDate, formatDuration } from "../../lib/format";
import { colors, radius, space } from "../../theme";
import { getConfig, listFields, saveProfile, type Guest } from "./api";
import { meKey, useConfig, useMe } from "./queries";
import { Status, StatusScreen } from "./Status";
const t = tr.onboarding;
export default function Onboarding() {
  const config = useConfig(),
    me = useMe(),
    fields = useQuery({
      queryKey: ["fields"],
      queryFn: listFields,
      retry: false,
      networkMode: "always",
    });
  if (!config.data || !me.data || !fields.data)
    return (
      <StatusScreen
        error={config.error ?? me.error ?? fields.error}
        retry={() => {
          void config.refetch();
          void me.refetch();
          void fields.refetch();
        }}
      />
    );
  return (
    <OnboardingForm config={config.data} fields={fields.data} guest={me.data} />
  );
}
export function OnboardingForm({
  config,
  fields,
  guest,
}: {
  config: Awaited<ReturnType<typeof getConfig>>;
  fields: Awaited<ReturnType<typeof listFields>>;
  guest: Guest;
}) {
  const cache = useQueryClient();
  const [field, setField] = useState(guest.profile?.field_id ?? "");
  const [minutes, setMinutes] = useState<30 | 60 | 90>(
    guest.profile?.daily_minutes ?? 60,
  );
  const [attempt, setAttempt] = useState<"first" | "repeat">(
    guest.profile?.attempt_kind ?? "first",
  );
  const selected = fields.find((f) => f.id === field);
  const save = useMutation({
    networkMode: "always",
    mutationFn: async (destination: "/placement" | "/today") => {
      const profile = await saveProfile({
        field_id: field,
        daily_minutes: minutes,
        attempt_kind: attempt,
      });
      cache.setQueryData<Guest>(meKey, { ...guest, profile });
      return destination;
    },
    onSuccess: (dest) =>
      dest === "/today" ? router.replace(dest) : router.push(dest),
  });
  const disabled = !selected || save.isPending;
  return (
    <Screen
      contentStyle={s.body}
      footerStyle={s.footer}
      footer={
        <>
          {save.error && (
            <Status
              error={save.error}
              retry={() => save.mutate(save.variables ?? "/placement")}
            />
          )}
          <Button
            label={t.start}
            disabled={disabled}
            onPress={() => save.mutate("/placement")}
          />
          <Label
            variant="meta"
            weight={400}
            color={colors.inkMuted}
            style={s.center}
          >
            {t.meta}
          </Label>
          <Button
            variant="text"
            underline
            label={t.explore}
            disabled={disabled}
            onPress={() => save.mutate("/today")}
          />
        </>
      }
    >
      <View style={s.row}>
        <Label variant="onboardingWordmark" color={colors.primary}>
          {config.app_name}
        </Label>
        <Chip
          tone="butter"
          style={s.examChip}
          label={t.exam(formatDate(config.exam_date))}
        />
      </View>
      <View style={s.intro}>
        <Label accessibilityRole="header" variant="intro">
          {t.title}
        </Label>
        <Label variant="lead" color={colors.inkMuted}>
          {t.intro}
        </Label>
      </View>
      <Card style={s.form}>
        <View style={s.group}>
          <SelectField
            label={t.field}
            value={field}
            options={[
              { value: "", label: tr.draft.chooseField },
              ...fields.map((f) => ({ value: f.id, label: f.name })),
            ]}
            onChange={setField}
          />
          {selected && (
            <View style={s.hint}>
              <Label variant="meta" weight={600} color={colors.aquaInk}>
                {
                  { P1: tr.draft.scoreP1, P2: t.scoreP2, P3: tr.draft.scoreP3 }[
                    selected.score_type
                  ]
                }
              </Label>
            </View>
          )}
        </View>
        <View style={s.choice}>
          <Label variant="tileTitle">{t.minutes}</Label>
          <ChoicePills
            label={t.minutes}
            value={String(minutes)}
            options={([30, 60, 90] as const).map((n) => ({
              label: formatDuration(n),
              value: String(n),
            }))}
            onChange={(n) => setMinutes(Number(n) as 30 | 60 | 90)}
          />
        </View>
        <View style={s.choice}>
          <Label variant="tileTitle">{t.attempt}</Label>
          <ChoicePills
            label={t.attempt}
            value={attempt}
            options={[
              { value: "first", label: t.first },
              { value: "repeat", label: t.repeat },
            ]}
            onChange={setAttempt}
          />
        </View>
      </Card>
    </Screen>
  );
}
const s = StyleSheet.create({
  body: { paddingTop: space.x24, gap: 0 },
  footer: { gap: space.x8, paddingBottom: space.x16 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x12,
  },
  intro: { gap: space.x8, marginTop: space.x22 },
  examChip: { paddingVertical: space.x7, paddingHorizontal: space.x12 },
  form: {
    marginTop: space.x20,
    padding: space.x18,
    borderRadius: radius.primary,
    gap: space.x18,
  },
  group: { gap: space.x8 },
  choice: { gap: space.x10 },
  hint: {
    backgroundColor: colors.aqua,
    borderRadius: radius.compact,
    paddingVertical: space.x8,
    paddingHorizontal: space.x12,
  },
  center: { textAlign: "center" },
});
