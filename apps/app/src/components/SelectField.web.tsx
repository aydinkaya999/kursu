import { useId } from "react";
import { View } from "react-native";
import { colors, line, radius, size, space } from "../theme";
import { useWebTextStyle } from "../theme/webTypography";
import type { ChoiceProps } from "./Choices";
export function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
}: ChoiceProps<T>) {
  const id = useId();
  const title = useWebTextStyle("tileTitle"),
    field = useWebTextStyle("rowTitle", 600);
  return (
    <View style={{ gap: space.x8 }}>
      <label htmlFor={id} style={{ ...title, color: colors.ink }}>
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(event) => {
          const selected = options.find(
            (option) => option.value === event.target.value,
          );
          if (selected) onChange(selected.value);
        }}
        style={{
          ...field,
          boxSizing: "border-box",
          width: "100%",
          minHeight: size.action,
          paddingInline: space.x14,
          border: line.control + "px solid " + colors.borderField,
          borderRadius: radius.field,
          backgroundColor: colors.surface,
          color: colors.ink,
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </View>
  );
}
