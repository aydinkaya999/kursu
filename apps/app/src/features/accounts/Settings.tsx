import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { Button, Card, Label, Screen } from "../../components/Core";
import { ChoicePills } from "../../components/Choices";
import { tr } from "../../i18n/tr";
import { formatDuration } from "../../lib/format";
import { Status, StatusScreen } from "../placement/Status";
import { useMe } from "../placement/queries";
import { getSettings, saveSettings, signOut, type Preferences } from "./api";
import { Input } from "./Forms";
const t = tr.account;
export default function Settings() {
  const me = useMe(),
    q = useQuery({
      queryKey: ["settings"],
      queryFn: getSettings,
      enabled: !!me.data?.profile,
      retry: false,
      networkMode: "always",
    });
  if (!me.data || (me.data.profile && !q.data))
    return (
      <StatusScreen
        error={me.error ?? q.error}
        retry={() => {
          void me.refetch();
          void q.refetch();
        }}
      />
    );
  return (
    <SettingsForm key={me.data.id} initial={q.data} guest={me.data.is_guest} />
  );
}
export function SettingsForm({
  initial,
  guest,
}: {
  initial?: Preferences;
  guest: boolean;
}) {
  const cache = useQueryClient(),
    [minutes, setMinutes] = useState(initial?.daily_minutes ?? 60),
    [time, setTime] = useState(initial?.notification_time?.slice(0, 5) ?? "");
  const [legal, setLegal] = useState<"terms" | "privacy" | null>(null),
    [confirm, setConfirm] = useState(false),
    [saved, setSaved] = useState(false);
  const valid = time === "" || /^([01]\d|2[0-3]):[0-5]\d$/.test(time);
  const save = useMutation({
    networkMode: "always",
    mutationFn: () =>
      saveSettings({ daily_minutes: minutes, notification_time: time || null }),
    onSuccess: async (value) => {
      cache.setQueryData(["settings"], value);
      setSaved(true);
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["me"] }),
        cache.invalidateQueries({ queryKey: ["today"] }),
      ]);
    },
  });
  const leave = useMutation({
    networkMode: "always",
    mutationFn: signOut,
    onSuccess: async () => {
      await cache.cancelQueries();
      cache.clear();
      router.replace("/");
    },
  });
  return (
    <Screen>
      <Label variant="h1" accessibilityRole="header">
        {t.settings}
      </Label>
      {initial && (
        <Card>
          <Label variant="tileTitle">{t.minutes}</Label>
          <ChoicePills
            label={t.minutes}
            options={([30, 60, 90] as const).map((n) => ({
              value: String(n),
              label: formatDuration(n),
            }))}
            value={String(minutes)}
            onChange={(v) => {
              setMinutes(Number(v) as Preferences["daily_minutes"]);
              setSaved(false);
            }}
          />
          <Input
            label={t.notify}
            placeholder={t.timeHint}
            value={time}
            onChangeText={(v) => {
              setTime(v);
              setSaved(false);
            }}
            maxLength={5}
          />
          {!valid && <Label>{t.timeError}</Label>}
          <Button
            label={t.save}
            disabled={!valid || save.isPending}
            onPress={() => save.mutate()}
          />
          {saved && <Label accessibilityLiveRegion="polite">{t.saved}</Label>}
          {save.error && <Status error={save.error} />}
        </Card>
      )}
      <Card>
        <Label>{t.disclosure}</Label>
        {(["privacy", "terms"] as const).map((k) => (
          <Button
            variant="text"
            key={k}
            label={t[k]}
            onPress={() => setLegal(k === legal ? null : k)}
          />
        ))}
        {legal && (
          <Label>
            {t[legal]} · {legal === "terms" ? t.refund : t.consent} ·{" "}
            {t.legalPending}
          </Label>
        )}
      </Card>
      {guest ? (
        <Button label={t.title} onPress={() => router.push("/auth")} />
      ) : (
        <Card>
          <Button
            variant="secondary"
            label={t.logout}
            disabled={leave.isPending}
            onPress={() => leave.mutate(false)}
          />
          {confirm && <Label>{t.confirm}</Label>}
          <Button
            variant="text"
            label={t.remove}
            disabled={leave.isPending}
            onPress={() => (confirm ? leave.mutate(true) : setConfirm(true))}
          />
          {confirm && (
            <Button
              label={t.cancel}
              variant="text"
              onPress={() => setConfirm(false)}
            />
          )}
        </Card>
      )}
      {leave.error && <Status error={leave.error} />}
      <Button
        variant="text"
        label={tr.nav.back}
        onPress={() => router.dismissTo("/today")}
      />
    </Screen>
  );
}
