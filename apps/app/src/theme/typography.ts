import { createContext, useContext } from "react";
import type { TextStyle } from "react-native";
export const FontContext = createContext(false);
export type Weight = 400 | 500 | 600 | 700 | 800;
export const families = {
  400: "JakartaRegular",
  500: "JakartaMedium",
  600: "JakartaSemibold",
  700: "JakartaBold",
  800: "JakartaExtraBold",
} as const;
function type(
  fontSize: number,
  lineHeight: number,
  weight: Weight,
  letterSpacing = 0,
) {
  return { fontSize, lineHeight, weight, letterSpacing };
}
export const typography = {
  notebookTitle: type(22, 28, 800, -0.22),
  notebookStatus: type(16, 21, 800),
  notebookHint: type(12.5, 18, 400),
  todayWide: type(32, 40, 800, -0.32),
  dayCount: type(17, 22, 800),
  feedbackTitle: type(17, 24, 800),
  dayPercent: type(22, 26, 800),
  resultNet: type(44, 48, 800, -0.88),
  resultNote: type(12, 17, 400),
  planTopic: type(13.5, 20, 400),
  onboardingWordmark: type(24, 30, 800, -0.48),
  display: type(42, 48, 800, -0.84),
  h1: type(26, 32, 800, -0.26),
  intro: type(28, 34, 800, -0.28),
  lessonTitle: type(21, 27, 800, -0.21),
  screenTitle: type(22, 28, 800),
  compactTitle: type(19, 26, 800),
  navTitle: type(15, 20, 800),
  h2: type(15, 20, 800),
  tileTitle: type(14, 20, 800),
  question: type(17, 26, 600),
  practice: type(15.5, 23, 600),
  body: type(14, 21, 400),
  lead: type(15, 22, 400),
  rowTitle: type(15, 20, 700),
  meta: type(13, 18, 500),
  caption: type(12, 16, 700),
  small: type(12.5, 17, 600),
  button: type(16, 22, 800),
  secondary: type(15, 20, 800),
  link: type(14, 20, 700),
  table: type(13.5, 19, 600),
  wordmark: type(26, 32, 800, -0.52),
} as const;
export type TextRole = keyof typeof typography;
export function useTextStyle(role: TextRole, override?: Weight): TextStyle {
  const ready = useContext(FontContext);
  const { weight: defaultWeight, ...metrics } = typography[role];
  const weight = override ?? defaultWeight;
  return {
    ...metrics,
    ...(ready ? { fontFamily: families[weight] } : { fontWeight: weight }),
  };
}
