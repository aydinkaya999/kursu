import { router } from "expo-router";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { RequestFailure } from "../../lib/session";

export type Destination = {
  from?: string;
  source?: string;
  attemptId?: string;
  counter?: string;
};
export const wallRoute = (params: Destination) => ({
  pathname: "/paywall" as const,
  params,
});
export function limitRoute(error: unknown, from: string) {
  return wallRoute({
    from,
    source: "limit",
    counter: error instanceof RequestFailure ? error.counter : undefined,
  });
}
export function isLimit(error: unknown) {
  return (
    error instanceof RequestFailure &&
    (error.code === "entitlement_required" ||
      error.code === "free_limit_reached")
  );
}
export function leaveWall({ from, attemptId, source }: Destination) {
  if (from === "result" && attemptId)
    router.dismissTo({
      pathname: "/mock/[attemptId]/result",
      params: { attemptId },
    });
  else if (
    from === "mock" ||
    from === "notebook" ||
    from === "lessons" ||
    from === "photo"
  )
    router.dismissTo(`/${from}`);
  else if (source === "limit")
    router.dismissTo({ pathname: "/today", params: { preview: "closed" } });
  else router.dismissTo("/today");
}
// OAuth may reload the page or launch a fresh native route. Bind return context
// to the existing provider state and consume it only on that flow's callback.
export async function storeReturn(state: string, intent: Destination) {
  const key = "kursu.checkout." + state,
    value = JSON.stringify(intent);
  if (Platform.OS === "web") window.sessionStorage.setItem(key, value);
  else await SecureStore.setItemAsync(key, value);
}
export async function takeReturn(
  state: string,
): Promise<Destination | undefined> {
  const key = "kursu.checkout." + state;
  const raw =
    Platform.OS === "web"
      ? window.sessionStorage.getItem(key)
      : await SecureStore.getItemAsync(key);
  if (!raw) return;
  if (Platform.OS === "web") window.sessionStorage.removeItem(key);
  else await SecureStore.deleteItemAsync(key);
  return JSON.parse(raw) as Destination;
}
