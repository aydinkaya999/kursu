import { useQueryClient } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { openAuthSessionAsync } from "expo-web-browser";
import { useCallback, useEffect, useRef, useState } from "react";
import { Platform } from "react-native";
import { Screen, Label, Button, Card } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { Input } from "./Forms";
import {
  startEmail,
  verifyEmail,
  startProvider,
  finishProvider,
  type Provider,
} from "./api";
import {
  leaveWall,
  storeReturn,
  takeReturn,
  wallRoute,
  type Destination,
} from "../commerce/navigation";
import { getMe } from "../placement/api";

const t = tr.account;
export default function AuthScreen() {
  const cache = useQueryClient();
  const { provider, state, cancel, next, from, source, attemptId, counter } =
    useLocalSearchParams<
      Destination & {
        next?: string;
        provider?: Provider;
        state?: string;
        cancel?: string;
      }
    >();
  const [step, setStep] = useState<"choose" | "email" | "code">("choose");
  const [email, setEmail] = useState(""),
    [code, setCode] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const running = useRef(false),
    handled = useRef("");
  const finish = useCallback(
    async (oauthState?: string) => {
      await cache.cancelQueries();
      cache.getMutationCache().clear();
      await cache.resetQueries();
      const me = await getMe();
      cache.setQueryData(["me"], me);
      const saved = oauthState ? await takeReturn(oauthState) : undefined;
      if (next === "paywall" || saved)
        router.replace(
          wallRoute(saved ?? { from, source, attemptId, counter }),
        );
      else router.replace(me.profile ? "/today" : "/onboarding");
    },
    [cache, next, from, source, attemptId, counter],
  );
  const run = useCallback(async (action: () => Promise<void>) => {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      const status = e instanceof RequestFailure ? e.status : 0;
      setError(
        status === 400
          ? t.invalid
          : status === 429
            ? t.wait
            : status === 503
              ? t.providerUnavailable
              : tr.shared.error,
      );
    } finally {
      running.current = false;
      setBusy(false);
    }
  }, []);
  useEffect(() => {
    if (
      state &&
      !cancel &&
      (provider === "google" || provider === "apple") &&
      handled.current !== state
    ) {
      handled.current = state;
      void run(async () => {
        await finishProvider(provider, state);
        await finish(state);
      });
    }
  }, [provider, state, cancel, finish, run]);
  const social = (provider: Provider) =>
    run(async () => {
      const info = await startProvider(provider);
      if (next === "paywall")
        await storeReturn(info.state, { from, source, attemptId, counter });
      if (Platform.OS === "web") {
        window.location.assign(info.authorization_url);
        return;
      }
      const result = await openAuthSessionAsync(
        info.authorization_url,
        "kursu://auth",
      );
      if (result.type === "success") {
        const url = new URL(result.url);
        if (
          url.searchParams.get("state") !== info.state ||
          url.searchParams.has("cancel")
        )
          return;
        handled.current = info.state;
        await finishProvider(provider, info.state);
        await finish(info.state);
      }
    });
  const send = () =>
    run(async () => {
      await startEmail(email.trim());
      setCode("");
      setStep("code");
    });
  return (
    <Screen>
      <Label variant="h1" accessibilityRole="header">
        {t.title}
      </Label>
      <Label>{t.intro}</Label>
      <Card>
        {step === "choose" ? (
          <>
            <Button
              label={t.email}
              disabled={busy}
              onPress={() => setStep("email")}
            />
            {(["google", "apple"] as const).map((p) => (
              <Button
                key={p}
                variant="secondary"
                label={t[p]}
                disabled={busy}
                onPress={() => void social(p)}
              />
            ))}
          </>
        ) : step === "email" ? (
          <>
            <Input
              label={t.emailAddress}
              testID="account-email"
              value={email}
              onChangeText={setEmail}
              autoComplete="email"
              keyboardType="email-address"
            />
            <Button
              label={t.next}
              disabled={busy || !email.trim()}
              onPress={() => void send()}
            />
          </>
        ) : (
          <>
            <Label>{email}</Label>
            <Input
              label={t.code}
              testID="account-code"
              keyboardType="number-pad"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChangeText={setCode}
            />
            <Button
              label={t.next}
              disabled={busy || !/^\d{6}$/.test(code)}
              onPress={() =>
                void run(async () => {
                  await verifyEmail(email.trim(), code);
                  await finish();
                })
              }
            />
            <Button
              variant="text"
              label={t.resend}
              disabled={busy}
              onPress={() => void send()}
            />
          </>
        )}
        {step !== "choose" && (
          <Button
            variant="text"
            label={t.cancel}
            disabled={busy}
            onPress={() => {
              setStep("choose");
              setError("");
            }}
          />
        )}
        {error && <Label accessibilityRole="alert">{error}</Label>}
      </Card>
      <Button
        variant="text"
        underline
        label={tr.result.guest}
        disabled={busy}
        onPress={() =>
          next === "paywall" && source !== "placement"
            ? leaveWall({ from, source, attemptId, counter })
            : router.replace("/today")
        }
      />
    </Screen>
  );
}
