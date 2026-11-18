import { createApiClient } from "@kursu/api-client";

export const client = createApiClient(
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000",
);

export async function getHealth(signal: AbortSignal) {
  const response = await client["/v1/health"].get({ signal });
  if (response.status !== 200) {
    throw new Error(`Health request failed (HTTP ${response.status})`);
  }
  return response.json();
}
