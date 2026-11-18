import { useState, type ReactNode } from "react";
import {
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type PressableProps,
  type StyleProp,
  type TextProps,
  type ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  colors,
  line,
  radius,
  shadow,
  size,
  space,
  useTextStyle,
  type TextRole,
  type Weight,
} from "../theme";
import { Icon, type IconName } from "./Icon";
export function Label({
  variant = "body",
  weight,
  color = colors.ink,
  figures = false,
  style,
  ...props
}: TextProps & {
  variant?: TextRole;
  weight?: Weight;
  color?: string;
  figures?: boolean;
}) {
  return (
    <Text
      {...props}
      style={[
        useTextStyle(variant, weight),
        { color, flexShrink: 1 },
        figures && styles.figures,
        style,
      ]}
    />
  );
}
export function Action({
  style,
  children,
  disabled,
  accessibilityRole = "button",
  onFocus,
  onBlur,
  ...props
}: Omit<PressableProps, "style" | "children"> & {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <Pressable
      {...props}
      accessibilityRole={accessibilityRole}
      disabled={disabled}
      accessibilityState={{ ...props.accessibilityState, disabled: !!disabled }}
      onFocus={(event) => {
        setFocused(true);
        onFocus?.(event);
      }}
      onBlur={(event) => {
        setFocused(false);
        onBlur?.(event);
      }}
      style={({ pressed }) => [
        styles.target,
        style,
        pressed && styles.pressed,
        disabled && styles.disabled,
        focused && Platform.OS === "web" && styles.focus,
      ]}
    >
      {children}
    </Pressable>
  );
}
export function Screen({
  children,
  footer,
  inShell = false,
  contentStyle,
  footerStyle,
}: {
  children: ReactNode;
  footer?: ReactNode;
  inShell?: boolean;
  contentStyle?: StyleProp<ViewStyle>;
  footerStyle?: StyleProp<ViewStyle>;
}) {
  return (
    <SafeAreaView
      edges={inShell ? [] : ["top", "bottom", "left", "right"]}
      style={styles.screen}
    >
      <ScrollView
        style={styles.grow}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={[styles.column, contentStyle]}>{children}</View>
      </ScrollView>
      {footer && (
        <View style={[styles.column, styles.footer, footerStyle]}>
          {footer}
        </View>
      )}
    </SafeAreaView>
  );
}
export function Card({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}
export function PrimaryCard({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.primaryCard, style]}>{children}</View>;
}
type ButtonVariant = "primary" | "secondary" | "text" | "quiet";
export function Button({
  label,
  onPress,
  variant = "primary",
  disabled = false,
  compact = false,
  underline = false,
  style,
}: {
  label: string;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  compact?: boolean;
  underline?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const textRole: TextRole =
    compact || variant === "secondary"
      ? "secondary"
      : variant === "primary"
        ? "button"
        : variant === "quiet"
          ? "meta"
          : "link";
  return (
    <Action
      accessibilityLabel={label}
      onPress={onPress}
      disabled={disabled}
      style={[
        styles.button,
        buttonStyles[variant],
        compact && styles.compact,
        style,
      ]}
    >
      <Label
        variant={textRole}
        weight={variant === "quiet" ? 600 : variant === "text" ? 700 : 800}
        color={
          variant === "primary"
            ? colors.onPrimary
            : variant === "quiet"
              ? colors.inkMuted
              : variant === "text"
                ? colors.primary
                : colors.primaryStrong
        }
        style={[
          styles.centerText,
          (underline || variant === "quiet") && styles.underline,
        ]}
      >
        {label}
      </Label>
    </Action>
  );
}
export function IconButton({
  name,
  label,
  onPress,
  disabled = false,
}: {
  name: IconName;
  label: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Action
      accessibilityLabel={label}
      onPress={onPress}
      disabled={disabled}
      style={styles.iconButton}
    >
      <Icon name={name} />
    </Action>
  );
}
const buttonStyles = StyleSheet.create({
  primary: {
    minHeight: size.primaryAction,
    backgroundColor: colors.primary,
    boxShadow: shadow.primary,
  },
  secondary: { minHeight: size.action, backgroundColor: colors.primaryTint },
  text: { minHeight: size.target },
  quiet: { minHeight: size.target },
});
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.ground },
  grow: { flex: 1 },
  content: { flexGrow: 1, alignItems: "center" },
  column: {
    width: "100%",
    maxWidth: size.column,
    padding: space.x20,
    gap: space.x14,
  },
  footer: { alignSelf: "center", paddingTop: space.x8 },
  target: {
    minHeight: size.target,
    minWidth: size.target,
    justifyContent: "center",
  },
  pressed: { opacity: 0.8 },
  disabled: { opacity: 0.5 },
  focus: {
    outlineWidth: line.selected,
    outlineColor: colors.primaryStrong,
    outlineStyle: "solid",
    outlineOffset: 2,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: space.x16,
    gap: space.x10,
    boxShadow: shadow.card,
  },
  primaryCard: {
    backgroundColor: colors.primary,
    borderRadius: radius.primary,
    padding: space.x18,
    gap: space.x12,
    boxShadow: shadow.primary,
  },
  button: {
    alignItems: "center",
    borderRadius: radius.pill,
    paddingHorizontal: space.x16,
    paddingVertical: space.x6,
  },
  compact: { minHeight: size.compactAction, boxShadow: "none" },
  centerText: { textAlign: "center" },
  underline: { textDecorationLine: "underline" },
  iconButton: {
    width: size.target,
    height: size.target,
    alignItems: "center",
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    boxShadow: shadow.control,
  },
  figures: { fontVariant: ["tabular-nums"] },
});
