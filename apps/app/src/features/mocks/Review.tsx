import { useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { View } from "react-native";
import { AnswerRow } from "../../components/Choices";
import { Button, Card, IconButton, Label, Screen } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { StudyStatus } from "../study/StudyStatus";
import { sourceName } from "../study/StudyCard";
import { review } from "./api";
import { resultRoute, s } from "./shared";
export default function Review() {
  const { attemptId: id, filter } = useLocalSearchParams<{
    attemptId: string;
    filter?: string;
  }>();
  const q = useQuery({
    queryKey: ["mock-review", id],
    queryFn: () => review(id),
    retry: false,
  });
  const [index, setIndex] = useState(0);
  const back = () => router.dismissTo(resultRoute(id));
  const items = q.data?.filter(
    (i) =>
      filter !== "wrong" || (i.selected != null && i.selected !== i.correct),
  );
  const item = items?.[index];
  if (!item || !items)
    return (
      <StudyStatus
        error={q.error ?? (items ? new Error() : undefined)}
        retry={() => void q.refetch()}
        onBack={back}
      />
    );
  return (
    <Screen
      footer={
        <View style={s.row}>
          <Button
            style={s.grow}
            variant="secondary"
            label={tr.study.previous}
            disabled={index === 0}
            onPress={() => setIndex(index - 1)}
          />
          <Button
            style={s.grow}
            label={index + 1 === items.length ? tr.mock.result : tr.mock.next}
            onPress={() =>
              index + 1 === items.length ? back() : setIndex(index + 1)
            }
          />
        </View>
      }
    >
      <View style={s.between}>
        <IconButton name="back" label={tr.mock.result} onPress={back} />
        <Label variant="navTitle">
          {tr.placement.count(index + 1, items.length)}
        </Label>
      </View>
      <Label variant="practice">{item.question.stem}</Label>
      {(["A", "B", "C", "D", "E"] as const).map((l) => (
        <AnswerRow
          key={l}
          letter={l}
          label={item.question.options[l]}
          state={
            l === item.correct
              ? "correct"
              : l === item.selected
                ? "wrong"
                : "other"
          }
        />
      ))}
      <Card style={s.stack}>
        <Label variant="h2">
          {item.selected && item.selected !== item.correct
            ? tr.study.whyWrong
            : tr.controls.correct}
        </Label>
        {item.rationales.map((r) => (
          <Label key={r.option}>{r.option + ") " + r.text}</Label>
        ))}
        {item.steps.length > 0 && <Label variant="h2">{tr.study.steps}</Label>}
        {item.steps.map((step, i) => (
          <View key={i}>
            <Label weight={700}>{step.title}</Label>
            <Label>{step.text}</Label>
          </View>
        ))}
        <Label variant="meta">
          {tr.study.feedbackSource(sourceName(item.source))}
        </Label>
        {item.source.kind === "law" && item.source.quote && (
          <Label>{item.source.quote}</Label>
        )}
      </Card>
    </Screen>
  );
}
