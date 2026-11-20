import { Image, StyleSheet, View } from "react-native";
import { Action, Card, Label } from "../../components/Core";
import { Icon } from "../../components/Icon";
import { Chip } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { colors, line, radius, size, space } from "../../theme";
import type { Solution } from "./api";

const t = tr.photo;
export function PhotoResult({
  solution,
  onLesson,
}: {
  solution: Solution;
  onLesson: (id: string) => void;
}) {
  const r = solution.result,
    lesson = r.lesson;
  return (
    <>
      <View style={s.preview}>
        <Image
          accessible
          accessibilityLabel={t.captured}
          source={{ uri: "data:image/jpeg;base64," + solution.preview_jpeg }}
          resizeMode="contain"
          style={s.image}
        />
        <Label variant="meta" weight={700} color={colors.inkMuted}>
          {t.captured}
        </Label>
      </View>
      {r.state === "solved" ? (
        <>
          <Card style={s.card}>
            <View style={s.row}>
              <Label variant="caption" color={colors.primaryStrong}>
                {t.question}
              </Label>
              {r.is_placeholder && <Chip label={t.demo} tone="surface" />}
            </View>
            <Label variant="lead" weight={600} selectable>
              {r.question}
            </Label>
          </Card>
          <Card style={s.card}>
            <View style={s.caution}>
              <Icon name="info" size={space.x14} color={colors.butterInk} />
              <Label variant="caption" color={colors.butterInk}>
                {t.caution}
              </Label>
            </View>
            {r.steps?.map((step, i) => (
              <View key={i} style={s.step}>
                <View style={s.number}>
                  <Label
                    variant="meta"
                    weight={800}
                    color={colors.primaryStrong}
                  >
                    {i + 1}
                  </Label>
                </View>
                <View style={s.details}>
                  <Label variant="tileTitle">{step.title}</Label>
                  <Label selectable variant="planTopic" color={colors.inkMuted}>
                    {step.text}
                  </Label>
                </View>
              </View>
            ))}
            <View style={[s.row, s.answer]}>
              <Label variant="meta" weight={800} color={colors.mintInk}>
                {t.answer}
              </Label>
              <Label variant="compactTitle" color={colors.mintInk} selectable>
                {r.answer}
              </Label>
            </View>
          </Card>
        </>
      ) : (
        <Card style={s.card}>
          <Label variant="h2">
            {r.state === "low_confidence" ? t.low : t.outside}
          </Label>
          {r.state === "low_confidence" && r.topic && (
            <Label>{t.topic(r.topic)}</Label>
          )}
        </Card>
      )}
      {r.state !== "out_of_scope" && lesson && (
        <Action
          accessibilityRole="link"
          accessibilityLabel={t.related(lesson.title)}
          onPress={() => onLesson(lesson.id)}
          style={s.link}
        >
          <Label variant="link" color={colors.primary}>
            {t.related(lesson.title)}
          </Label>
        </Action>
      )}
    </>
  );
}
const s = StyleSheet.create({
  preview: {
    minHeight: size.photoPreview,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: space.x8,
    backgroundColor: colors.surface,
    borderColor: colors.borderField,
    borderWidth: line.selected,
    borderStyle: "dashed",
    borderRadius: radius.task,
  },
  image: { height: size.cell, width: size.photoPreview },
  caution: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: space.x6,
    backgroundColor: colors.butter,
    paddingVertical: space.x4,
    paddingHorizontal: space.x10,
    borderRadius: radius.pill,
  },
  card: {
    borderRadius: radius.task,
    paddingHorizontal: space.x16,
    paddingVertical: space.x14,
    gap: space.x12,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: space.x12,
    flexWrap: "wrap",
  },
  step: { flexDirection: "row", alignItems: "flex-start", gap: space.x12 },
  details: { flex: 1, gap: space.x2 },
  number: {
    width: size.stepBadge,
    height: size.stepBadge,
    borderRadius: radius.pill,
    backgroundColor: colors.primaryTint,
    justifyContent: "center",
    alignItems: "center",
  },
  answer: {
    backgroundColor: colors.mint,
    borderRadius: radius.field,
    paddingHorizontal: space.x14,
    paddingVertical: space.x10,
  },
  link: { minHeight: size.target, justifyContent: "center" },
});
