import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { colors, line, radius, size, space } from "../theme";
import { Action, Label } from "./Core";
import { Icon } from "./Icon";
import type { ChoiceProps } from "./Choices";
export function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
}: ChoiceProps<T>) {
  const [open, setOpen] = useState(false);
  return (
    <View style={styles.group}>
      <Label variant="tileTitle">{label}</Label>
      <Action
        accessibilityLabel={label}
        accessibilityValue={{
          text: options.find((option) => option.value === value)?.label,
        }}
        accessibilityState={{ expanded: open }}
        onPress={() => setOpen(!open)}
        style={styles.field}
      >
        <Label variant="rowTitle" weight={600}>
          {options.find((option) => option.value === value)?.label}
        </Label>
        <Icon name="chevron" size={16} />
      </Action>
      {open && (
        <View style={styles.menu}>
          {options.map((option) => (
            <Action
              key={option.value}
              accessibilityLabel={option.label}
              accessibilityState={{ selected: option.value === value }}
              onPress={() => {
                onChange(option.value);
                setOpen(false);
              }}
              style={styles.item}
            >
              <Label>{option.label}</Label>
              {option.value === value && (
                <Icon name="check" size={16} color={colors.primaryStrong} />
              )}
            </Action>
          ))}
        </View>
      )}
    </View>
  );
}
const styles = StyleSheet.create({
  group: { gap: space.x8 },
  field: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: size.action,
    borderWidth: line.control,
    borderColor: colors.borderField,
    borderRadius: radius.field,
    backgroundColor: colors.surface,
    paddingHorizontal: space.x14,
  },
  menu: {
    borderWidth: line.hair,
    borderColor: colors.line,
    borderRadius: radius.field,
    paddingHorizontal: space.x12,
    backgroundColor: colors.surface,
  },
  item: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
});
