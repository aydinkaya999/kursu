import { useMutation, useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { Button, Card, Label, Screen } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { isLimit, limitRoute } from "../commerce/navigation";
import { Status } from "../placement/Status";
import * as api from "./api";
import { History, resultRoute, s } from "./shared";
const t = tr.mock;
export default function Home() {
  const { exam } = useLocalSearchParams<{ exam?: string }>();
  const list = useQuery({ queryKey: ["mocks"], queryFn: api.catalogue });
  const history = useQuery({
    queryKey: ["mock-history"],
    queryFn: api.history,
  });
  const start = useMutation({
    mutationFn: ({ id, mode }: { id: string; mode: api.Mode }) =>
      api.start(id, { mode }),
    onError: (error) => {
      if (isLimit(error)) router.push(limitRoute(error, "mock"));
    },
    onSuccess: (a) =>
      router.push(
        a.submitted_at
          ? resultRoute(a.id)
          : { pathname: "/mock/[attemptId]", params: { attemptId: a.id } },
      ),
  });
  return (
    <Screen inShell>
      <Label variant="h1" accessibilityRole="header">
        {tr.nav.mock}
      </Label>
      {!list.data && (
        <Status error={list.error} retry={() => void list.refetch()} />
      )}
      {start.error && !isLimit(start.error) && (
        <Status
          error={start.error}
          retry={() => {
            if (start.variables) start.mutate(start.variables);
          }}
        />
      )}
      {list.data
        ?.filter((m) => !exam || m.id === exam)
        .map((m) => (
          <Card key={m.id} style={s.stack}>
            <Label variant="h2">{m.title}</Label>
            <Label variant="meta">{t.meta}</Label>
            <Button
              label={t.timed}
              disabled={start.isPending}
              onPress={() => start.mutate({ id: m.id, mode: "timed" })}
            />
            <Button
              label={t.practice}
              variant="secondary"
              disabled={start.isPending}
              onPress={() => start.mutate({ id: m.id, mode: "practice" })}
            />
          </Card>
        ))}
      {history.data ? (
        <History items={history.data} />
      ) : (
        <Status error={history.error} retry={() => void history.refetch()} />
      )}
    </Screen>
  );
}
