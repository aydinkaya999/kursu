import { useState, type ReactNode } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Button, Card, IconButton, Label, Screen } from "../../components/Core";
import {
  Chip,
  InfoBox,
  Pill,
  SegmentedProgress,
} from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { colors, radius, size, space } from "../../theme";
import { Status } from "../placement/Status";
import { type Lesson } from "./api";
const t = tr.study;
export function sourceName(source: Lesson["source"], short = false): string {
  if (source.kind === "lesson") return source.lesson_title;
  if (source.kind === "notes")
    return short ? source.title : source.title + " · " + source.section;
  if (short) return source.short_name;
  const numbers =
    source.articles?.join(t.conjunction) ?? String(source.article ?? "");
  return (
    (source.name || source.short_name) +
    (numbers ? ", " + t.articles(numbers) : "")
  );
}
export function Sheet({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <Modal transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={s.backdrop}
        testID="study-sheet"
      >
        <SafeAreaView edges={["bottom"]} style={s.sheet}>
          <View style={s.heading}>
            <Label variant="h2" accessibilityRole="header">
              {title}
            </Label>
            <IconButton name="cross" label={t.close} onPress={onClose} />
          </View>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={s.sheetBody}
          >
            {children}
          </ScrollView>
        </SafeAreaView>
      </KeyboardAvoidingView>
    </Modal>
  );
}
export function StudyCard({
  lesson,
  index,
  onNext,
  onBack,
  onPrevious,
  nextLabel,
  backLabel,
  busy = false,
  error,
  retry,
}: {
  lesson: Lesson;
  index: number;
  onNext: () => void;
  onBack: () => void;
  onPrevious?: () => void;
  nextLabel: string;
  backLabel: string;
  busy?: boolean;
  error?: unknown;
  retry?: () => void;
}) {
  const [sourceOpen, setSourceOpen] = useState(false);
  const card = lesson.cards[index]!;
  return (
    <Screen
      contentStyle={s.page}
      footer={
        <>
          {error ? <Status error={error} retry={retry} /> : null}
          <View style={s.controls}>
            {onPrevious && (
              <Button
                label={t.previous}
                variant="secondary"
                style={s.prev}
                disabled={index === 0 || busy}
                onPress={onPrevious}
              />
            )}
            <Button
              label={nextLabel}
              style={s.next}
              disabled={busy}
              onPress={onNext}
            />
          </View>
        </>
      }
    >
      <View style={s.heading}>
        <IconButton name="back" label={backLabel} onPress={onBack} />
        <Label variant="navTitle">{t.micro}</Label>
        <Pill label={tr.placement.count(index + 1, lesson.cards.length)} />
      </View>
      <SegmentedProgress
        done={index + 1}
        total={lesson.cards.length}
        label={t.cardProgress}
      />
      <Card style={s.lesson}>
        <Chip
          tone="aqua"
          label={lesson.subtest + " · " + sourceName(lesson.source, true)}
        />
        <View style={{ gap: space.x4 }}>
          <Label variant="meta" weight={800} color={colors.peachInk}>
            {t.kinds[card.kind]}
          </Label>
          <Label variant="lessonTitle" accessibilityRole="header">
            {card.title}
          </Label>
        </View>
        {card.blocks.map((b, i) => (
          <View key={i} style={[s.block, i % 2 === 1 && s.tinted]}>
            <Label
              variant="tileTitle"
              color={i % 2 === 1 ? colors.primaryStrong : colors.ink}
            >
              {b.heading}
            </Label>
            <Label>{b.text}</Label>
          </View>
        ))}
        {card.tip && (
          <InfoBox tone="butter" icon="lightbulb" label={card.tip} />
        )}
        <View style={s.sourceRow}>
          <Label
            variant="small"
            weight={400}
            color={colors.inkMuted}
            style={{ flex: 1 }}
          >
            {t.source(sourceName(lesson.source))}
          </Label>
          {lesson.source.kind === "law" && lesson.source.quote && (
            <Button
              variant="text"
              label={t.articleText}
              onPress={() => setSourceOpen(true)}
            />
          )}
        </View>
      </Card>
      {sourceOpen && lesson.source.kind === "law" && (
        <Sheet title={t.articleText} onClose={() => setSourceOpen(false)}>
          <Label weight={700}>{sourceName(lesson.source)}</Label>
          <Label>{lesson.source.quote}</Label>
        </Sheet>
      )}
    </Screen>
  );
}
const s = StyleSheet.create({
  page: { paddingTop: space.x16, gap: space.x12 },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x12,
  },
  controls: { flexDirection: "row", gap: space.x10 },
  prev: { flex: 1 },
  next: { flex: 2 },
  lesson: {
    borderRadius: radius.nav,
    padding: space.x18,
    paddingBottom: space.x8,
    gap: space.x12,
  },
  block: {
    borderRadius: radius.option,
    paddingHorizontal: space.x14,
    paddingVertical: space.x12,
    gap: space.x4,
    backgroundColor: colors.neutralTint,
  },
  tinted: { backgroundColor: colors.primaryTint },
  sourceRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.x10,
    minHeight: size.target,
  },
  backdrop: {
    flex: 1,
    backgroundColor: colors.scrim,
    justifyContent: "flex-end",
    alignItems: "center",
  },
  sheet: {
    borderTopLeftRadius: radius.nav,
    borderTopRightRadius: radius.nav,
    backgroundColor: colors.surface,
    width: "100%",
    maxWidth: size.column,
    maxHeight: "85%",
    padding: space.x20,
    gap: space.x10,
  },
  sheetBody: { gap: space.x12, paddingBottom: space.x12 },
});
