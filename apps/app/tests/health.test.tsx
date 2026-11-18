import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react-native";

import { tr } from "../src/i18n/tr";

const fetchHealth = jest.spyOn(globalThis, "fetch");
// The generated client captures fetch when the screen's module first loads.
const { default: HealthScreen } =
  jest.requireActual<typeof import("../app/index")>("../app/index");

async function renderHealth() {
  const client = new QueryClient({
    defaultOptions: { queries: { gcTime: Infinity } },
  });
  await render(
    <QueryClientProvider client={client}>
      <HealthScreen />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchHealth.mockReset();
});

afterAll(() => {
  fetchHealth.mockRestore();
});

it("shows a pending check while the request is in flight", async () => {
  const pending = Promise.withResolvers<Response>();
  fetchHealth.mockReturnValueOnce(pending.promise);
  await renderHealth();
  expect(screen.getByText(tr.health.pending)).toBeVisible();
  expect(screen.queryByText(tr.health.ok)).toBeNull();
  expect(fetchHealth).toHaveBeenCalledWith(
    expect.stringMatching(/\/v1\/health$/),
    expect.objectContaining({ method: "GET" }),
  );
  await act(() =>
    pending.resolve(new Response(JSON.stringify({ status: "ok" }))),
  );
  expect(await screen.findByText(tr.health.ok)).toBeVisible();
});

it("retries an unavailable service and displays its successful reply", async () => {
  fetchHealth
    .mockResolvedValueOnce(new Response(null, { status: 503 }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ status: "ok" })));
  await renderHealth();
  expect(await screen.findByText(tr.health.error)).toBeVisible();
  await fireEvent.press(screen.getByRole("button", { name: tr.health.retry }));
  expect(await screen.findByText(tr.health.ok)).toBeVisible();
  expect(fetchHealth).toHaveBeenCalledTimes(2);
});
