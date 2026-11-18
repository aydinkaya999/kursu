import { TextInput, StyleSheet, View, type TextInputProps } from "react-native";
import { Label } from "../../components/Core";
import { colors, space, line, radius, size, useTextStyle } from "../../theme";
export function Input({ label, ...props }: TextInputProps & { label: string }) {
  const font = useTextStyle("body");
  return (
    <View style={styles.group}>
      <Label variant="tileTitle">{label}</Label>
      <TextInput
        accessibilityLabel={label}
        autoCapitalize="none"
        autoCorrect={false}
        {...props}
        style={[styles.input, font]}
      />
    </View>
  );
}
const styles = StyleSheet.create({
  group: { gap: space.x6 },
  input: {
    color: colors.ink,
    backgroundColor: colors.surface,
    borderWidth: line.control,
    borderColor: colors.borderField,
    borderRadius: radius.field,
    minHeight: size.target,
    paddingHorizontal: space.x12,
  },
});
