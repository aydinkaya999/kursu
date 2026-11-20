import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { randomUUID } from "expo-crypto";
import { getPendingResultAsync } from "expo-image-picker";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { Platform, View } from "react-native";
import { Button, Card, IconButton, Label, Screen } from "../../components/Core";
import { Pill } from "../../components/Indicators";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { colors, space } from "../../theme";
import { Input } from "../accounts/Forms";
import { isLimit, limitRoute, wallRoute } from "../commerce/navigation";
import { Status } from "../placement/Status";
import { useConfig, useMe } from "../placement/queries";
import { Sheet } from "../study/StudyCard";
import { getPhoto, reportPhoto, solvePhoto } from "./api";
import { Camera } from "./Camera";
import { Picker, selectedImage } from "./Picker";
import { PhotoResult } from "./PhotoResult";
import { usePhotoQuota } from "./queries";

const t = tr.photo;

function Report({ id, close }: { id: string; close: () => void }) {
  const [text, setText] = useState("");
  const report = useMutation({
    mutationFn: () => reportPhoto(id, text.trim()),
    gcTime: 0,
    retry: false,
  });
  return (
    <Sheet title={t.report} onClose={close}>
      {report.isSuccess ? (
        <Label accessibilityLiveRegion="polite">{tr.study.thanks}</Label>
      ) : (
        <>
          <Input
            label={tr.study.reportPrompt}
            value={text}
            onChangeText={setText}
            maxLength={1000}
            multiline
          />
          <Button
            label={tr.study.send}
            disabled={!text.trim() || report.isPending}
            onPress={() => report.mutate()}
          />
          {report.error && <Status error={report.error} />}
        </>
      )}
    </Sheet>
  );
}

export default function PhotoScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const owner = useMe(),
    config = useConfig(),
    cache = useQueryClient();
  const quota = usePhotoQuota(owner.data?.id, config.dataUpdatedAt);
  const [message, setMessage] = useState("");
  const [report, setReport] = useState(false);
  const query = useQuery({
    queryKey: ["photo", owner.data?.id, id],
    queryFn: () => getPhoto(id!),
    enabled: !!id && !!owner.data,
    retry: false,
    gcTime: 0,
  });
  const focused = useRef(true);
  useFocusEffect(
    useCallback(() => {
      focused.current = true;
      return () => {
        focused.current = false;
      };
    }, []),
  );
  const submission = useMutation({
    mutationFn: solvePhoto,
    retry: false,
    gcTime: 0,
    networkMode: "always",
    onSuccess: (solution) => {
      cache.setQueryData(["photo", owner.data?.id, solution.id], solution);
      if (focused.current) router.setParams({ id: solution.id });
    },
    onError: (error) => {
      if (focused.current && isLimit(error))
        router.push(limitRoute(error, "photo"));
    },
    onSettled: () => cache.invalidateQueries({ queryKey: ["photo-quota"] }),
  });
  const submit = submission.mutate;
  useEffect(() => {
    if (Platform.OS !== "android" || id || !owner.data?.id) return;
    let live = true;
    void getPendingResultAsync()
      .then((pending) => {
        if (!live || !pending) return;
        if ("code" in pending) {
          setMessage(t.invalid);
          return;
        }
        const image = selectedImage(pending);
        if (image) submit({ request_id: randomUUID(), image });
      })
      .catch(() => {
        if (live) setMessage(t.invalid);
      });
    return () => {
      live = false;
    };
  }, [owner.data?.id, id, submit]);
  const sending = useRef(false);
  const start = (image: string) => {
    if (sending.current) return;
    setMessage("");
    sending.current = true;
    submit(
      { request_id: randomUUID(), image },
      {
        onSettled: () => {
          sending.current = false;
        },
      },
    );
  };
  const back = () => router.dismissTo("/today");
  const solution = !query.error ? query.data : undefined;
  const depleted = quota.data?.remaining === 0;
  const paywall = () =>
    router.push(
      wallRoute({ from: "photo", source: "limit", counter: "photos" }),
    );
  const again = () => {
    setReport(false);
    setMessage("");
    submission.reset();
    if (depleted && quota.data?.period === "lifetime") paywall();
    else router.replace("/photo");
  };
  const failure = submission.error;
  const status = failure instanceof RequestFailure ? failure.status : undefined;
  const issue =
    message ||
    (status === 422 || status === 413
      ? t.invalid
      : status === 503
        ? t.unavailable
        : "");
  const busy = submission.isPending;
  return (
    <Screen
      contentStyle={{ gap: space.x12 }}
      footer={
        solution ? (
          <>
            <Button label={t.again} onPress={again} />
            <Button
              label={t.report}
              variant="quiet"
              underline
              onPress={() => setReport(true)}
            />
          </>
        ) : undefined
      }
    >
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          gap: space.x8,
        }}
      >
        <IconButton name="back" label={tr.study.backToday} onPress={back} />
        <Label accessibilityRole="header" variant="navTitle">
          {t.title}
        </Label>
        {quota.data && (
          <Pill label={t.rights(quota.data.remaining)} tone="rose" />
        )}
      </View>
      {id ? (
        solution ? (
          <PhotoResult
            solution={solution}
            onLesson={(lessonId) =>
              router.push({
                pathname: "/lessons/[lessonId]",
                params: { lessonId, review: "1", from: "photo" },
              })
            }
          />
        ) : query.error instanceof RequestFailure &&
          query.error.status === 404 ? (
          <Card>
            <Label>{t.gone}</Label>
            <Button label={t.again} onPress={again} />
          </Card>
        ) : (
          <Status
            error={query.error ?? owner.error}
            retry={() => void (owner.data ? query.refetch() : owner.refetch())}
          />
        )
      ) : !quota.data || quota.error ? (
        <Status
          error={quota.error ?? owner.error}
          retry={() => void (owner.data ? quota.refetch() : owner.refetch())}
        />
      ) : depleted ? (
        <Card>
          <Label>{quota.data.period === "day" ? t.dailyEnd : t.freeEnd}</Label>
          {quota.data.period === "lifetime" && (
            <Button label={tr.commerce.see} onPress={paywall} />
          )}
        </Card>
      ) : (
        <Card>
          <Camera disabled={busy} onImage={start} onError={setMessage} />
          <Picker disabled={busy} onImage={start} onError={setMessage} />
          {busy && (
            <Label accessibilityLiveRegion="polite">{t.processing}</Label>
          )}
          {issue ? (
            <Label accessibilityRole="alert" color={colors.dangerInk}>
              {issue}
            </Label>
          ) : null}
        </Card>
      )}
      {!id && failure && status !== 403 && status !== 422 && status !== 413 && (
        <Status
          error={failure}
          retry={() => {
            if (submission.variables) submit(submission.variables);
          }}
        />
      )}
      {report && solution && (
        <Report id={solution.id} close={() => setReport(false)} />
      )}
    </Screen>
  );
}
