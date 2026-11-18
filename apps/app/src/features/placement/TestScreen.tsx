import { useQuery, useQueryClient } from "@tanstack/react-query";
import { randomUUID } from "expo-crypto";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import {
  Action,
  Button,
  IconButton,
  Label,
  Screen,
} from "../../components/Core";
import { OptionButton } from "../../components/Choices";
import { Chip, Pill, ProgressBar } from "../../components/Indicators";
import { Icon } from "../../components/Icon";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { colors, line, radius, size, space } from "../../theme";
import {
  answerPlacement,
  startPlacement,
  type Answer,
  type Attempt,
} from "./api";
import { useMe, meKey } from "./queries";
import { Status, StatusScreen } from "./Status";
const t = tr.placement;
export default function TestScreen() {
  const params = useLocalSearchParams<{ kind?: string }>(),
    kind = params.kind === "short" ? "short" : "full";
  const cache = useQueryClient(),
    me = useMe();
  const key = ["placement", kind] as const;
  const query = useQuery({
    queryKey: key,
    queryFn: () => startPlacement(kind),
    enabled: !!me.data?.profile,
    retry: false,
    networkMode: "always",
    refetchOnWindowFocus: false,
  });
  if (me.data && !me.data.profile) return <Redirect href="/onboarding" />;
  const attempt = query.data;
  if (!attempt || (attempt.state === "completed" && query.isFetching))
    return (
      <StatusScreen
        error={query.error ?? me.error}
        retry={() => {
          if (me.data) void query.refetch();
          else void me.refetch();
        }}
      />
    );
  if (attempt.state === "completed")
    return (
      <Redirect
        href={{ pathname: "/placement/result", params: { id: attempt.id } }}
      />
    );
  if (!attempt.question)
    return <StatusScreen error={true} retry={() => void query.refetch()} />;
  return (
    <Question
      key={attempt.question.id}
      attempt={attempt}
      question={attempt.question}
      onClose={() => {
        void cache.invalidateQueries({ queryKey: meKey });
        if (router.canGoBack()) router.back();
        else router.replace("/today");
      }}
      onSubmit={async (data) => {
        try {
          const next = await answerPlacement(attempt.id, data);
          cache.setQueryData(key, next);
          if (next.state === "completed")
            void cache.invalidateQueries({ queryKey: meKey });
        } catch (error) {
          if (error instanceof RequestFailure && error.status === 409)
            await query.refetch();
          throw error;
        }
      }}
    />
  );
}
type Letter = keyof NonNullable<Attempt["question"]>["options"];
const letters: readonly Letter[] = ["A", "B", "C", "D", "E"];
export function Question({
  attempt,
  question,
  onClose,
  onSubmit,
}: {
  attempt: Attempt;
  question: NonNullable<Attempt["question"]>;
  onClose: () => void;
  onSubmit: (data: Answer) => Promise<void>;
}) {
  const [selected, select] = useState<Letter | null>(null),
    [unsure, setUnsure] = useState(false);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>();
  const sending = useRef(false),
    pending = useRef<Answer | null>(null);
  const send = async (data: Answer) => {
    if (sending.current) return;
    sending.current = true;
    pending.current = data;
    setBusy(true);
    setError(undefined);
    try {
      await onSubmit(data);
    } catch (e) {
      setError(e);
    } finally {
      sending.current = false;
      setBusy(false);
    }
  };
  const submit = (choice: Letter | null) =>
    void send({
      question_id: question.id,
      selected_option: choice,
      not_sure: unsure,
      client_answer_id: randomUUID(),
    });
  return (
    <Screen
      contentStyle={s.body}
      footerStyle={s.footer}
      footer={
        <>
          {error ? (
            <Status
              error={error}
              retry={() => {
                if (pending.current) void send(pending.current);
              }}
            />
          ) : null}
          <Button
            label={t.next}
            disabled={busy || selected === null || !!error}
            onPress={() => submit(selected)}
          />
        </>
      }
    >
      <View style={s.header}>
        <IconButton
          name="cross"
          label={t.close}
          onPress={onClose}
          disabled={busy}
        />
        <Label variant="navTitle">{t.title}</Label>
        <Pill label={t.count(attempt.position, attempt.total)} />
      </View>
      <View style={s.progress}>
        <ProgressBar
          label={t.progress}
          value={attempt.position}
          max={attempt.total}
        />
      </View>
      <View style={s.subject}>
        <Chip label={attempt.subtest ?? ""} style={s.subjectChip} />
      </View>
      <Label variant="question" style={s.stem}>
        {question.stem}
      </Label>
      <View role="group" accessibilityLabel={t.options} style={s.options}>
        {letters.map((letter) => (
          <OptionButton
            key={letter}
            letter={letter}
            label={question.options[letter]}
            selected={selected === letter}
            onPress={() => {
              if (!busy && !error) select(letter);
            }}
          />
        ))}
      </View>
      <View style={s.questionActions}>
        <Action
          accessibilityRole="checkbox"
          accessibilityLabel={t.unsure}
          accessibilityState={{ checked: unsure }}
          disabled={busy || !!error}
          onPress={() => setUnsure(!unsure)}
          style={s.toggle}
        >
          <View style={[s.checkbox, unsure && s.checked]}>
            {unsure && (
              <Icon
                name="check"
                color={colors.onPrimary}
                size={size.checkbox - space.x4}
              />
            )}
          </View>
          <Label weight={600}>{t.unsure}</Label>
        </Action>
        <Button
          variant="text"
          label={t.blank}
          style={s.blank}
          disabled={busy || !!error}
          onPress={() => submit(null)}
        />
      </View>
    </Screen>
  );
}
const s = StyleSheet.create({
  body: { paddingTop: space.x16, gap: 0 },
  footer: { gap: space.x8 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x12,
  },
  progress: { marginTop: space.x14 },
  subject: { marginTop: space.x18 },
  subjectChip: { paddingVertical: space.x6, paddingHorizontal: space.x12 },
  blank: { paddingHorizontal: space.x6 },
  stem: { marginTop: space.x12 },
  options: { gap: space.x10, marginTop: space.x16 },
  questionActions: {
    marginTop: space.x10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x12,
  },
  toggle: { flexDirection: "row", gap: space.x10, alignItems: "center" },
  checkbox: {
    width: size.checkbox,
    height: size.checkbox,
    borderWidth: line.control,
    borderColor: colors.borderField,
    borderRadius: radius.tiny,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  checked: { borderColor: colors.primary, backgroundColor: colors.primary },
});
