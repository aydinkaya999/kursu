import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react-native";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { Platform } from "react-native";
import { Camera } from "../src/features/photo/Camera";
import { Picker } from "../src/features/photo/Picker";
import { PhotoResult } from "../src/features/photo/PhotoResult";
import PhotoScreen from "../src/features/photo/PhotoScreen";
import {
  getPhoto,
  solvePhoto,
  reportPhoto,
  type Solution,
} from "../src/features/photo/api";
import { getPhotoQuota } from "../src/features/photo/api";
import { tr } from "../src/i18n/tr";
import appConfig from "../app.json";
import example from "../../../content/seed/photo-example.json";

jest.mock("expo-image-picker", () => ({
  UIImagePickerPreferredAssetRepresentationMode: { Compatible: "compatible" },
  launchImageLibraryAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  requestCameraPermissionsAsync: jest.fn(),
  getPendingResultAsync: jest.fn(),
}));
const mockParams: { id?: string } = {};
jest.mock("expo-router", () => ({
  router: {
    push: jest.fn(),
    replace: jest.fn(),
    setParams: jest.fn(),
    dismissTo: jest.fn(),
  },
  useLocalSearchParams: () => mockParams,
  useFocusEffect: jest.fn(),
}));
jest.mock("expo-crypto", () => ({ randomUUID: () => "submission-id" }));
jest.mock("../src/features/photo/api");
jest.mock("../src/features/placement/queries", () => ({
  useMe: () => ({ data: { id: "owner" } }),
  useConfig: () => ({ dataUpdatedAt: 1 }),
}));
const t = tr.photo;
const button = (name: string) => screen.getByRole("button", { name });
const solution: Solution = {
  id: "private",
  preview_jpeg: "AA==",
  result: {
    state: "solved",
    is_placeholder: true,
    question: example.question,
    steps: example.steps,
    answer: example.answer,
    topic: "Mevzuat",
    lesson: { id: "lesson", title: "Örnek ders" },
  },
};
const image: ImagePicker.ImagePickerSuccessResult = {
  canceled: false,
  assets: [
    { uri: "file:///photo.jpg", width: 10, height: 10, base64: "image-bytes" },
  ],
};
beforeEach(() => {
  jest.clearAllMocks();
  delete mockParams.id;
  jest
    .mocked(getPhotoQuota)
    .mockResolvedValue({ remaining: 2, period: "lifetime" });
  jest.mocked(getPhoto).mockResolvedValue(solution);
});
async function show() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  await render(
    <QueryClientProvider client={client}>
      <PhotoScreen />
    </QueryClientProvider>,
  );
}
test("native camera and library handle permission, cancellation and the selected image", async () => {
  const onImage = jest.fn(),
    onError = jest.fn();
  const props = { onImage, onError, disabled: false };
  await render(
    <>
      <Camera {...props} />
      <Picker {...props} />
    </>,
  );
  jest.mocked(ImagePicker.requestCameraPermissionsAsync).mockResolvedValueOnce({
    granted: false,
  } as ImagePicker.PermissionResponse);
  await fireEvent.press(button(t.take));
  expect(onError).toHaveBeenCalledWith(t.cameraPermission);
  expect(ImagePicker.launchCameraAsync).not.toHaveBeenCalled();
  jest
    .mocked(ImagePicker.requestCameraPermissionsAsync)
    .mockResolvedValueOnce({ granted: true } as ImagePicker.PermissionResponse);
  jest.mocked(ImagePicker.launchCameraAsync).mockResolvedValueOnce(image);
  await fireEvent.press(button(t.take));
  expect(onImage).toHaveBeenCalledWith("image-bytes");
  jest
    .mocked(ImagePicker.launchImageLibraryAsync)
    .mockResolvedValueOnce({ canceled: true, assets: null })
    .mockResolvedValueOnce(image);
  await fireEvent.press(button(t.upload));
  expect(onImage).toHaveBeenCalledTimes(1);
  await fireEvent.press(button(t.upload));
  expect(onImage).toHaveBeenCalledTimes(2);
  expect(appConfig.expo.plugins).toContainEqual([
    "expo-image-picker",
    {
      cameraPermission: t.cameraPermission,
      photosPermission: t.photoPermission,
      microphonePermission: false,
    },
  ]);
});
test("Android recovers the selected photo after the picker recreates the activity", async () => {
  const platform = jest.replaceProperty(Platform, "OS", "android");
  try {
    jest.mocked(ImagePicker.getPendingResultAsync).mockResolvedValueOnce(image);
    jest.mocked(solvePhoto).mockResolvedValueOnce(solution);
    await show();
    await waitFor(() =>
      expect(router.setParams).toHaveBeenCalledWith({ id: solution.id }),
    );
    expect(jest.mocked(solvePhoto).mock.calls[0]?.[0]).toEqual({
      request_id: "submission-id",
      image: "image-bytes",
    });
  } finally {
    platform.restore();
  }
});

test("a network retry reuses its request ID and opens the private result", async () => {
  jest
    .mocked(solvePhoto)
    .mockRejectedValueOnce(new TypeError("offline"))
    .mockResolvedValueOnce(solution);
  jest.mocked(ImagePicker.launchImageLibraryAsync).mockResolvedValueOnce(image);
  await show();
  await fireEvent.press(await screen.findByRole("button", { name: t.upload }));
  await fireEvent.press(
    await screen.findByRole("button", { name: tr.health.retry }),
  );
  await waitFor(() =>
    expect(router.setParams).toHaveBeenCalledWith({ id: solution.id }),
  );
  expect(jest.mocked(solvePhoto).mock.calls.map(([data]) => data)).toEqual(
    Array(2).fill({ request_id: "submission-id", image: "image-bytes" }),
  );
});
test("the solution labels the demo, opens the lesson and sends an owner report", async () => {
  mockParams.id = solution.id;
  jest.mocked(reportPhoto).mockResolvedValue({ received: true });
  await show();
  expect(await screen.findByText(t.caution)).toBeVisible();
  expect(screen.getByText(t.demo)).toBeVisible();
  await fireEvent.press(
    screen.getByRole("link", { name: t.related("Örnek ders") }),
  );
  expect(router.push).toHaveBeenCalledWith({
    pathname: "/lessons/[lessonId]",
    params: { lessonId: "lesson", review: "1", from: "photo" },
  });
  await fireEvent.press(button(t.report));
  expect(button(tr.study.send)).toBeDisabled();
  await fireEvent.changeText(
    screen.getByLabelText(tr.study.reportPrompt),
    "  Örnek bildirim  ",
  );
  await fireEvent.press(button(tr.study.send));
  expect(await screen.findByText(tr.study.thanks)).toBeVisible();
  expect(reportPhoto).toHaveBeenCalledWith(solution.id, "Örnek bildirim");
});
test.each(["low_confidence", "out_of_scope"] as const)(
  "a %s result hides all proposed steps and answers",
  async (state) => {
    await render(
      <PhotoResult
        solution={{ ...solution, result: { ...solution.result, state } }}
        onLesson={jest.fn()}
      />,
    );
    expect(
      screen.getByText(state === "low_confidence" ? t.low : t.outside),
    ).toBeVisible();
    expect(screen.queryByText(example.answer)).toBeNull();
    expect(screen.queryByText(example.steps[0]!.title)).toBeNull();
    if (state === "low_confidence")
      expect(screen.getByRole("link")).toBeVisible();
    else expect(screen.queryByRole("link")).toBeNull();
  },
);
test.each(["lifetime", "day"] as const)(
  "an exhausted %s allowance gives the correct next action",
  async (period) => {
    jest.mocked(getPhotoQuota).mockResolvedValue({ remaining: 0, period });
    await show();
    expect(
      await screen.findByText(period === "day" ? t.dailyEnd : t.freeEnd),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: t.take })).toBeNull();
    if (period === "lifetime") {
      await fireEvent.press(button(tr.commerce.see));
      expect(router.push).toHaveBeenCalledWith({
        pathname: "/paywall",
        params: { from: "photo", source: "limit", counter: "photos" },
      });
    } else
      expect(
        screen.queryByRole("button", { name: tr.commerce.see }),
      ).toBeNull();
  },
);
