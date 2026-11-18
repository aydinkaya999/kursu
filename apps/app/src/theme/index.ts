export { colors } from "./colors";

export const spacing = { gap: 12, inset: 20 } as const;
export const control = { minHeight: 44, pillRadius: 999 } as const;
export const typography = {
  title: { fontSize: 22, lineHeight: 28, fontWeight: "800" },
  body: { fontSize: 14, lineHeight: 21 },
  action: { fontSize: 15, fontWeight: "700" },
} as const;
