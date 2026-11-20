import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, fireEvent, screen } from "@testing-library/react-native";
import { router } from "expo-router";
import Paywall, { PaywallView } from "../src/features/commerce/Paywall";
import { paywall, type Offer } from "../src/features/commerce/api";
import { tr } from "../src/i18n/tr";
import { formatUntilDate } from "../src/lib/format";
jest.mock("expo-router", () => ({
  router: { replace: jest.fn(), dismissTo: jest.fn() },
  useLocalSearchParams: () => ({ from: "notebook", source: "limit" }),
}));
jest.mock("../src/features/commerce/api");
jest.mock("../src/features/placement/queries", () => ({
  useMe: () => ({ data: { id: "candidate", is_guest: true } }),
}));
const offer: Offer = {
  platform: "web",
  amount_try: 745,
  results_date: "2028-06-11",
  access: { active: false, source: null, valid_until: null },
  limits: {
    lessons_per_day: 2,
    questions_per_day: 7,
    plan_days: 4,
    mock_exams: 3,
  },
  checkout_available: true,
  sandbox_receipt: null,
};
test("offer shows remote values and sends a guest through sign-in before checkout", async () => {
  jest.mocked(paywall).mockResolvedValue(offer);
  const cache = new QueryClient({
    defaultOptions: { queries: { gcTime: Infinity } },
  });
  await render(
    <QueryClientProvider client={cache}>
      <Paywall />
    </QueryClientProvider>,
  );
  await screen.findByText("₺745");
  expect(screen.getByText(tr.commerce.perDay(7))).toBeVisible();
  expect(screen.getByText(tr.commerce.first(4))).toBeVisible();
  expect(formatUntilDate(offer.results_date)).toBe("11 Haziran 2028'e");
  expect(formatUntilDate("2027-06-11")).toBe("11 Haziran 2027'ye");
  await fireEvent.press(screen.getByRole("button", { name: tr.commerce.buy }));
  expect(router.replace).toHaveBeenCalledWith(
    expect.objectContaining({
      pathname: "/auth",
      params: expect.objectContaining({ next: "paywall", from: "notebook" }),
    }),
  );
  await fireEvent.press(
    screen.getByRole("button", { name: tr.notebook.continueFree }),
  );
  expect(router.dismissTo).toHaveBeenCalledWith("/notebook");
});
test("a daily limit can be dismissed and an unavailable checkout cannot run", async () => {
  const close = jest.fn(),
    buy = jest.fn();
  await render(
    <PaywallView
      offer={{ ...offer, checkout_available: false }}
      busy={false}
      onBuy={buy}
      onClose={close}
      limit
    />,
  );
  expect(screen.getByText(tr.commerce.limit)).toBeVisible();
  await fireEvent.press(
    screen.getByRole("button", { name: tr.commerce.tomorrow }),
  );
  expect(close).toHaveBeenCalled();
  expect(screen.getByRole("button", { name: tr.commerce.buy })).toBeDisabled();
});
