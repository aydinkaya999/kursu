import { useFocusEffect, router } from "expo-router";
import { useCallback, useEffect } from "react";
import { Button, Card, Label } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { formatDate } from "../../lib/format";
import { useConfig, useMe } from "./queries";
import { Status } from "./Status";
export function TodayPlacement() {
  const config = useConfig(),
    me = useMe(),
    refresh = me.refetch;
  useFocusEffect(
    useCallback(() => {
      void refresh();
    }, [refresh]),
  );
  useEffect(() => {
    if (config.dataUpdatedAt) void refresh();
  }, [refresh, config.dataUpdatedAt]);
  const info = me.data?.placement;
  return (
    <Card>
      {config.data && (
        <Label variant="meta">
          {tr.onboarding.countdown(config.data.days_to_exam)}
        </Label>
      )}
      {!me.data || !config.data ? (
        <Status
          error={me.error ?? config.error}
          retry={() => {
            void refresh();
            void config.refetch();
          }}
        />
      ) : (
        <>
          {(!info?.latest_id || info.active_id) && (
            <Button
              label={info?.active_id ? tr.draft.resume : tr.onboarding.start}
              onPress={() =>
                router.push(me.data.profile ? "/placement" : "/onboarding")
              }
            />
          )}
          {info?.latest_id && (
            <Button
              variant="secondary"
              label={tr.draft.viewResult}
              onPress={() =>
                router.push({
                  pathname: "/placement/result",
                  params: { id: info.latest_id! },
                })
              }
            />
          )}
          {info?.can_retake && (
            <Button
              label={tr.draft.retake}
              onPress={() =>
                router.push({
                  pathname: "/placement",
                  params: { kind: "short" },
                })
              }
            />
          )}
          {info?.next_retake_on && !info.can_retake && !info.active_id && (
            <Label variant="meta">
              {tr.draft.retakeDate(formatDate(info.next_retake_on))}
            </Label>
          )}
        </>
      )}
    </Card>
  );
}
