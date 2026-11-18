import type { CSSProperties } from "react";
import { useTextStyle, type TextRole, type Weight } from "./typography";
export function useWebTextStyle(
  role: TextRole,
  weight?: Weight,
): CSSProperties {
  const text = useTextStyle(role, weight);
  return {
    fontFamily: text.fontFamily ?? "system-ui, sans-serif",
    fontSize: text.fontSize,
    lineHeight: String(text.lineHeight) + "px",
    fontWeight: text.fontWeight as CSSProperties["fontWeight"],
    letterSpacing: text.letterSpacing,
  };
}
