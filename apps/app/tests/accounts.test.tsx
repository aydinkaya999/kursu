import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import AuthScreen from "../src/features/accounts/AuthScreen";
import { SettingsForm } from "../src/features/accounts/Settings";
import {
  startEmail,
  saveSettings,
  signOut,
} from "../src/features/accounts/api";
import { tr } from "../src/i18n/tr";
import emailTemplate from "../../../services/api/app/modules/accounts/email.tr.json";
jest.mock("expo-router", () => ({
  useLocalSearchParams: () => ({}),
  router: { push: jest.fn(), replace: jest.fn() },
}));
jest.mock("expo-web-browser", () => ({ openAuthSessionAsync: jest.fn() }));
jest.mock("../src/features/accounts/api");
const t = tr.account;
test("the API email template matches the Turkish catalogue", () => {
  expect(emailTemplate).toEqual(tr.emailMessage);
});
function wrap(node: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { gcTime: Infinity },
      mutations: { gcTime: Infinity },
    },
  });
  return render(
    <QueryClientProvider client={client}>{node}</QueryClientProvider>,
  );
}
test("email sign-in asks for a six-digit code before continuing", async () => {
  await wrap(<AuthScreen />);
  await fireEvent.press(screen.getByText(t.email));
  await fireEvent.changeText(
    screen.getByLabelText(t.emailAddress),
    "user@example.org",
  );
  await fireEvent.press(screen.getByText(t.next));
  await waitFor(() =>
    expect(startEmail).toHaveBeenCalledWith("user@example.org"),
  );
  await waitFor(() => expect(screen.getByLabelText(t.code)).toBeVisible());
  expect(screen.getByRole("button", { name: t.next })).toBeDisabled();
});
test("settings validate the chosen time and require confirmation before deletion", async () => {
  await wrap(
    <SettingsForm
      initial={{ daily_minutes: 60, notification_time: null }}
      guest={false}
    />,
  );
  await fireEvent.changeText(screen.getByLabelText(t.notify), "27:00");
  expect(screen.getByRole("button", { name: t.save })).toBeDisabled();
  await fireEvent.changeText(screen.getByLabelText(t.notify), "10:30");
  await fireEvent.press(screen.getByText(t.save));
  await waitFor(() =>
    expect(saveSettings).toHaveBeenCalledWith({
      daily_minutes: 60,
      notification_time: "10:30",
    }),
  );
  await fireEvent.press(screen.getByText(t.remove));
  expect(signOut).not.toHaveBeenCalled();
  expect(screen.getByText(t.confirm)).toBeVisible();
  await fireEvent.press(screen.getByText(t.cancel));
  expect(screen.queryByText(t.confirm)).toBeNull();
});
