import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { AppState, View } from "react-native";
import {
  Action,
  Button,
  Card,
  IconButton,
  Label,
  Screen,
} from "../../components/Core";
import { OptionButton, OptionCell } from "../../components/Choices";
import { Chip, ProgressBar } from "../../components/Indicators";
import { Icon } from "../../components/Icon";
import { QuestionMap } from "../../components/Study";
import { tr } from "../../i18n/tr";
import { formatTimer, formatRange } from "../../lib/format";
import { colors, space } from "../../theme";
import { Status, StatusScreen } from "../placement/Status";
import { Sheet } from "../study/StudyCard";
import * as api from "./api";
import { s, resultRoute } from "./shared";
const t = tr.mock;

export function ExamView({
  a,
  seconds,
  busy,
  onSave,
  onMove,
  onSubmit,
  error,
  retry,
}: {
  a: api.Attempt;
  seconds: number | null;
  busy: boolean;
  onSave: (v: {
    selected_option?: api.Letter | null;
    flagged?: boolean;
  }) => void;
  onMove: (i: number) => void;
  onSubmit: () => void;
  error?: unknown;
  retry: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  const slot = a.questions[a.position - 1]!;
  const q = slot.question;
  const section = a.questions.filter((i) => i.subtest === slot.subtest);
  const compact = q && Object.values(q.options).every((o) => o.length <= 4);
  const Option = compact ? OptionCell : OptionButton;
  return (
    <Screen
      footer={
        <>
          {error ? <Status error={error} retry={retry} /> : null}
          <View style={s.row}>
            <Button
              style={s.grow}
              variant="secondary"
              label={tr.study.previous}
              disabled={busy || a.position === 1}
              onPress={() => onMove(a.position - 1)}
            />
            <Button
              style={s.grow}
              label={t.next}
              disabled={busy || a.position === a.questions.length}
              onPress={() => onMove(a.position + 1)}
            />
          </View>
          <Button
            variant="text"
            label={t.finish}
            disabled={busy}
            onPress={() => setConfirm(true)}
          />
        </>
      }
    >
      <Card style={s.examHeader}>
        <View style={s.grow}>
          <Label accessibilityRole="header" variant="h2">
            {a.title}
          </Label>
          <Label variant="meta">
            {t.count(a.position, a.questions.length, a.mode === "timed")}
          </Label>
        </View>
        <View role="timer" style={s.timer} accessibilityLabel={t.timer}>
          {seconds != null ? (
            <>
              <Label variant="timerDigits" figures color={colors.onPrimary}>
                {formatTimer(seconds)}
              </Label>
              <Label variant="caption" color={colors.onPrimaryMuted}>
                {t.left}
              </Label>
            </>
          ) : (
            <Label variant="meta" color={colors.onPrimary}>
              {t.untimed}
            </Label>
          )}
        </View>
        <IconButton
          name="cross"
          label={tr.placement.close}
          onPress={() => router.dismissTo("/mock")}
        />
      </Card>
      <ProgressBar
        label={tr.gallery.mockProgress}
        variant="mock"
        value={a.position}
        max={a.questions.length}
      />
      <View style={s.between}>
        <Chip label={slot.subtest} tone="primary" />
        <Action
          accessibilityLabel={t.flag}
          accessibilityState={{ selected: slot.flagged }}
          disabled={busy || !q}
          style={s.row}
          onPress={() => onSave({ flagged: !slot.flagged })}
        >
          <Icon
            name="flag"
            size={space.x16}
            color={slot.flagged ? colors.butterInk : colors.inkMuted}
          />
          <Label variant="meta">{t.flag}</Label>
        </Action>
      </View>
      {q ? (
        <>
          <Card>
            <Label variant="practice">{q.stem}</Label>
          </Card>
          <View
            role="group"
            accessibilityLabel={tr.placement.options}
            style={compact ? s.row : s.stack}
          >
            {(Object.keys(q.options) as api.Letter[]).map((l) => (
              <Option
                key={l}
                letter={l}
                label={q.options[l]}
                selected={slot.selected_option === l}
                onPress={() => {
                  if (!busy)
                    onSave({
                      selected_option: slot.selected_option === l ? null : l,
                    });
                }}
              />
            ))}
          </View>
        </>
      ) : (
        <Label>{tr.study.unavailable}</Label>
      )}
      <Card style={s.stack}>
        <Label variant="tileTitle">
          {slot.subtest +
            " · " +
            formatRange(
              section[0]!.position,
              section[section.length - 1]!.position,
            )}
        </Label>
        <View style={s.row}>
          <Chip tone="primary" label={tr.controls.answered} />
          <Chip tone="butter" label={tr.controls.flagged} />
        </View>
        <QuestionMap
          current={a.position}
          questions={section.map((i) => ({
            number: i.position,
            answered: i.selected_option != null,
            flagged: i.flagged,
          }))}
          onSelect={(i) => {
            if (!busy) onMove(i);
          }}
        />
      </Card>
      {confirm && (
        <Sheet title={t.confirm(a.blank)} onClose={() => setConfirm(false)}>
          <Button
            label={t.end}
            disabled={busy}
            onPress={() => {
              setConfirm(false);
              onSubmit();
            }}
          />
          <Button
            variant="secondary"
            label={t.resume}
            onPress={() => setConfirm(false)}
          />
        </Sheet>
      )}
    </Screen>
  );
}
export default function Exam() {
  const { attemptId: id } = useLocalSearchParams<{ attemptId: string }>();
  const cache = useQueryClient(),
    key = ["mock-attempt", id];
  const query = useQuery({
    queryKey: key,
    queryFn: () => api.attempt(id),
    retry: false,
    structuralSharing: false,
    refetchInterval: 30000,
  });
  const a = query.data;
  const { refetch } = query;
  const writing = useRef(false);
  const [seconds, setSeconds] = useState<number | null>(null);
  useEffect(() => {
    const sub = AppState.addEventListener("change", (state) => {
      if (state === "active" && !writing.current) void refetch();
    });
    return () => sub.remove();
  }, [refetch]);
  useEffect(() => {
    const initial = a?.remaining_seconds;
    if (initial == null || a?.submitted_at) return;
    const stamp = performance.now();
    let lastSync = -5;
    const tick = setInterval(() => {
      const elapsed = Math.floor((performance.now() - stamp) / 1000);
      const remaining = Math.max(0, initial - elapsed);
      setSeconds(remaining);
      if (remaining === 0 && elapsed - lastSync >= 5 && !writing.current) {
        lastSync = elapsed;
        void refetch();
      }
    }, 250);
    return () => clearInterval(tick);
  }, [a, refetch]);
  const mutation = useMutation({
    mutationFn: async (work: () => Promise<api.Attempt>) => {
      await cache.cancelQueries({ queryKey: key });
      return work();
    },
    onSuccess: (v) => cache.setQueryData(key, v),
    onSettled: () => {
      writing.current = false;
    },
  });
  const finish = useMutation({
    mutationFn: () => api.submit(id),
    onSuccess: () => router.replace(resultRoute(id)),
    onSettled: () => {
      writing.current = false;
    },
  });
  if (!a)
    return <StatusScreen error={query.error} retry={() => void refetch()} />;
  if (a.submitted_at) return <Redirect href={resultRoute(id)} />;
  function change(work: () => Promise<api.Attempt>) {
    if (writing.current) return;
    writing.current = true;
    mutation.mutate(work);
  }
  const question = a.questions[a.position - 1]?.question;
  return (
    <ExamView
      a={a}
      seconds={seconds ?? a.remaining_seconds ?? null}
      busy={mutation.isPending || finish.isPending || seconds === 0}
      onSave={(v) => {
        if (question) change(() => api.save(id, question.id, v));
      }}
      onMove={(i) => change(() => api.move(id, { position: i }))}
      onSubmit={() => {
        if (!writing.current) {
          writing.current = true;
          finish.mutate();
        }
      }}
      error={mutation.error ?? finish.error ?? query.error}
      retry={() => {
        if (mutation.error && mutation.variables) change(mutation.variables);
        else if (finish.error) finish.mutate();
        else void refetch();
      }}
    />
  );
}
