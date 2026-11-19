import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { StyleSheet, View } from "react-native";
import { Button, Card, IconButton, Label, Screen } from "../../components/Core";
import { AnswerRow } from "../../components/Choices";
import { Chip, Pill } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { colors, radius, space } from "../../theme";
import { Input } from "../accounts/Forms";
import { Status } from "../placement/Status";
import { reportQuestion, type Feedback } from "./api";
import { Sheet, sourceName } from "./StudyCard";
const t = tr.study;
export function Review({
  feedback: f,
  subject,
  position,
  total,
  busy,
  error,
  onNext,
  onBack,
  onLesson,
  retry,
}: {
  feedback: Feedback;
  subject: string;
  position: number;
  total: number;
  busy: boolean;
  error?: unknown;
  onNext: () => void;
  onBack: () => void;
  onLesson: (id: string) => void;
  retry: () => void;
}) {
  const [expanded, expand] = useState(false),
    [form, setForm] = useState(false),
    [text, setText] = useState("");
  const report = useMutation({
    networkMode: "always",
    mutationFn: () => reportQuestion(f.question.id, text.trim()),
    onSuccess: () => setForm(false),
  });
  const first = f.rationales[0];
  return (
    <Screen
      contentStyle={s.page}
      footer={
        <>
          {error ? <Status error={error} retry={retry} /> : null}
          <Button
            label={tr.placement.next}
            onPress={onNext}
            disabled={busy}
            style={s.next}
          />
        </>
      }
    >
      <View style={s.row}>
        <IconButton name="cross" label={tr.placement.close} onPress={onBack} />
        <Label variant="navTitle">{t.test(subject)}</Label>
        <Pill label={tr.placement.count(position, total)} />
      </View>
      <Label variant="practice">{f.question.stem}</Label>
      <View style={s.answers}>
        {(["A", "B", "C", "D", "E"] as const).map((l) => (
          <AnswerRow
            key={l}
            letter={l}
            label={f.question.options[l]}
            state={
              l === f.correct ? "correct" : l === f.selected ? "wrong" : "other"
            }
          />
        ))}
      </View>
      <Card style={s.card}>
        <View style={s.row}>
          <Label variant="feedbackTitle" accessibilityRole="header">
            {f.is_correct ? t.whyRight : t.whyWrong}
          </Label>
          {!f.is_correct && f.misconception_count > 0 && (
            <Chip tone="peach" label={t.misconception(f.misconception_count)} />
          )}
        </View>
        {first && <Label variant="planTopic">{first.text}</Label>}
        {f.steps.length > 0 && (
          <View style={s.details}>
            <Label variant="tileTitle">{t.steps}</Label>
            {f.steps.map((step, i) => (
              <View key={i} style={{ gap: space.x2 }}>
                <Label weight={700}>
                  {i + 1}. {step.title}
                </Label>
                <Label selectable>{step.text}</Label>
              </View>
            ))}
          </View>
        )}
        <View style={s.source}>
          <Label variant="caption" weight={800} color={colors.aquaInk}>
            {t.feedbackSource(sourceName(f.source))}
          </Label>
          {f.source.kind === "law" && f.source.quote && (
            <Label
              variant="meta"
              color={colors.aquaInk}
              style={{ fontStyle: "italic" }}
            >
              {f.source.quote}
            </Label>
          )}
        </View>
        {f.suggest_lesson && (
          <Label weight={700} color={colors.primaryStrong}>
            {t.recommended}
          </Label>
        )}
        <View style={s.links}>
          {f.related_lesson_id && (
            <Button
              variant="text"
              label={t.related}
              onPress={() => onLesson(f.related_lesson_id!)}
            />
          )}
          <Button
            variant="quiet"
            underline
            label={t.report}
            onPress={() => setForm(true)}
          />
        </View>
        {report.isSuccess && (
          <Label accessibilityLiveRegion="polite">{t.thanks}</Label>
        )}
        <Button
          variant="text"
          label={t.more}
          onPress={() => expand(!expanded)}
        />
        {expanded &&
          f.rationales.slice(1).map((r) => (
            <Label key={r.option}>
              {r.option}) {r.text}
            </Label>
          ))}
      </Card>
      {form && (
        <Sheet title={t.report} onClose={() => setForm(false)}>
          <Input
            label={t.reportPrompt}
            value={text}
            onChangeText={setText}
            multiline
            maxLength={1000}
          />
          <Button
            label={t.send}
            disabled={!text.trim() || report.isPending}
            onPress={() => report.mutate()}
          />
          {report.error && <Status error={report.error} />}
        </Sheet>
      )}
    </Screen>
  );
}
const s = StyleSheet.create({
  page: { paddingTop: space.x12, gap: space.x10 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x8,
  },
  answers: { gap: space.x6 },
  card: {
    paddingVertical: space.x14,
    paddingHorizontal: space.x16,
    gap: space.x8,
  },
  source: {
    paddingVertical: space.x10,
    paddingHorizontal: space.x12,
    backgroundColor: colors.aqua,
    borderRadius: radius.compact,
    gap: space.x4,
  },
  links: {
    flexDirection: "row",
    justifyContent: "space-between",
    flexWrap: "wrap",
    alignItems: "center",
  },
  details: { gap: space.x8 },
  next: { alignSelf: "flex-end", paddingHorizontal: space.x22 },
});
