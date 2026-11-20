import { createStore } from "zustand/vanilla";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { client } from "./api";

export class RequestFailure extends Error {
  constructor(
    readonly status: number,
    readonly code?: string,
    readonly counter?: string,
  ) {
    super("HTTP " + status);
  }
}
export function requireSuccess<R extends { status: number }>(
  response: R,
): asserts response is R & { status: 200 } {
  if (response.status !== 200) throw new RequestFailure(response.status);
}

export async function checkAccess(response: {
  status: number;
  json(): Promise<unknown>;
}) {
  if (response.status !== 403) return;
  const error = (await response.json()) as {
    code?: string;
    details?: { counter?: string };
  };
  throw new RequestFailure(response.status, error.code, error.details?.counter);
}

const web = Platform.OS === "web";
export const platform = web ? "web" : "native";
export const transport = {
  credentials: web ? ("include" as const) : ("omit" as const),
};
const key = "kursu.guest.refresh";
const memory = createStore<{ access: string | null }>(() => ({ access: null }));
let pending: Promise<string> | undefined;
const sessionChanges =
  web &&
  typeof window !== "undefined" &&
  typeof BroadcastChannel !== "undefined"
    ? new BroadcastChannel("kursu-account-changed")
    : undefined;
if (sessionChanges)
  sessionChanges.onmessage = () => window.location.replace("/");

async function credentials(initial: boolean) {
  const refresh = web ? null : await SecureStore.getItemAsync(key);
  async function acquire() {
    if (!initial || refresh) {
      const response = await client["/v1/auth/refresh"].post({
        ...transport,
        json: { platform, refresh_token: refresh },
      });
      if (response.status === 200) return response.json();
      if (response.status !== 401 || !initial)
        throw new RequestFailure(response.status);
    }
    const response = await client["/v1/auth/guest"].post({
      ...transport,
      json: { platform },
    });
    requireSuccess(response);
    return response.json();
  }
  return acceptTokens(await acquire());
}

export async function acceptTokens(tokens: {
  access_token: string;
  refresh_token?: string | null;
}) {
  if (!web && tokens.refresh_token)
    await SecureStore.setItemAsync(key, tokens.refresh_token);
  memory.setState({ access: tokens.access_token });
  return tokens.access_token;
}

export function notifyAccountChange() {
  sessionChanges?.postMessage("changed");
}

export async function forgetSession() {
  if (!web) await SecureStore.deleteItemAsync(key);
  memory.setState({ access: null });
  notifyAccountChange();
}

function renew(initial: boolean) {
  if (!pending) {
    const get = () => credentials(initial);
    const job =
      web && typeof navigator !== "undefined" && navigator.locks
        ? navigator.locks.request("kursu-session", get)
        : get();
    pending = job.finally(() => {
      pending = undefined;
    });
  }
  return pending;
}

export async function authorized<T>(
  call: (auth: {
    headers: { Authorization: `Bearer ${string}` };
  }) => Promise<T>,
): Promise<T> {
  const token = memory.getState().access ?? (await renew(true));
  const send = (access: string) =>
    call({ headers: { Authorization: `Bearer ${access}` } });
  try {
    return await send(token);
  } catch (error) {
    if (!(error instanceof RequestFailure) || error.status !== 401) throw error;
    const current = memory.getState().access;
    return send(current && current !== token ? current : await renew(false));
  }
}
