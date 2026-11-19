import { useQuery } from "@tanstack/react-query";
import { router, useFocusEffect } from "expo-router";
import { useCallback } from "react";
import { View } from "react-native";
import { Action, Button, Card, Label, Screen } from "../../components/Core";
import { Icon } from "../../components/Icon";
import { tr } from "../../i18n/tr";
import { formatDuration } from "../../lib/format";
import { colors, space } from "../../theme";
import { Status } from "../placement/Status";
import { library } from "./api";
import { useStartPractice } from "./navigation";
const t = tr.study;
export default function Library() {
  const q = useQuery({
    queryKey: ["study-library"],
    queryFn: library,
    retry: false,
    networkMode: "always",
  });
  const refresh = q.refetch;
  useFocusEffect(
    useCallback(() => {
      void refresh();
    }, [refresh]),
  );
  const begin = useStartPractice("lessons");
  return (
    <Screen inShell>
      <Label variant="screenTitle" accessibilityRole="header">
        {tr.nav.lessons}
      </Label>
      {!q.data && <Status error={q.error} retry={() => void refresh()} />}
      {begin.error && (
        <Status
          error={begin.error}
          retry={() => begin.variables && begin.mutate(begin.variables)}
        />
      )}
      {q.data?.map((section) => (
        <View key={section.name} style={{ gap: space.x12 }}>
          <Label variant="h2" accessibilityRole="header">
            {section.name}
          </Label>
          {section.topics.map((topic) => (
            <Card key={topic.id}>
              <Label variant="rowTitle">{topic.name}</Label>
              <Label variant="meta" color={colors.inkMuted}>
                {t.mastery[topic.mastery]}
              </Label>
              {topic.lessons.map((l) => (
                <Action
                  key={l.id}
                  accessibilityLabel={l.title}
                  onPress={() =>
                    router.push({
                      pathname: "/lessons/[lessonId]",
                      params: { lessonId: l.id, from: "lessons" },
                    })
                  }
                  style={{
                    flexDirection: "row",
                    gap: space.x10,
                    alignItems: "center",
                  }}
                >
                  <Icon
                    name={l.completed ? "check" : "book"}
                    color={l.completed ? colors.mintInk : colors.primary}
                  />
                  <View style={{ flex: 1 }}>
                    <Label weight={700}>{l.title}</Label>
                    <Label variant="meta">
                      {formatDuration(l.minutes)}
                      {l.completed && t.done}
                    </Label>
                  </View>
                  <Icon name="chevron" />
                </Action>
              ))}
              {topic.can_practice && (
                <Button
                  variant="secondary"
                  compact
                  label={t.beginTest}
                  disabled={begin.isPending}
                  onPress={() =>
                    begin.mutate({ kind: "topic_test", content_id: topic.id })
                  }
                />
              )}
            </Card>
          ))}
        </View>
      ))}
    </Screen>
  );
}
