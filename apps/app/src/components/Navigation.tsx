import { Link } from "expo-router";
import { StyleSheet, View } from "react-native";
import appConfig from "../../app.json";
import { tr, type Destination } from "../i18n/tr";
import { colors, radius, shadow, size, space } from "../theme";
import { Chip } from "./Indicators";
import { Action, Label } from "./Core";
import { Icon, type IconName } from "./Icon";

const items: Record<Destination, IconName> = {
  today: "calendar",
  lessons: "book",
  notebook: "notebook",
  mock: "stopwatch",
  progress: "chart",
};
const phone: readonly Destination[] = ["today", "lessons", "mock", "progress"];
export const destinations: readonly Destination[] = [
  "today",
  "lessons",
  "notebook",
  "mock",
  "progress",
];
type NavProps = {
  current: Destination;
  label?: string;
  onSelect?: (destination: Destination) => void;
};
function NavItems({
  current,
  onSelect,
  side,
}: {
  current: Destination;
  onSelect?: NavProps["onSelect"];
  side: boolean;
}) {
  return (side ? destinations : phone).map((destination) => {
    const active = current === destination;
    const color = active
      ? colors.primaryStrong
      : side
        ? colors.ink
        : colors.inkMuted;
    const icon = (
      <Icon name={items[destination]} color={color} size={side ? 20 : 22} />
    );
    const item = (
      <Action
        accessibilityRole={onSelect ? "button" : "link"}
        accessibilityLabel={tr.nav[destination]}
        accessibilityState={{ selected: active }}
        aria-current={active ? "page" : undefined}
        onPress={onSelect ? () => onSelect(destination) : undefined}
        style={
          side
            ? StyleSheet.flatten([styles.sideItem, active && styles.active])
            : styles.tabItem
        }
      >
        {side ? (
          icon
        ) : (
          <View style={[styles.iconPill, active && styles.active]}>{icon}</View>
        )}
        <Label
          variant={side ? "rowTitle" : "caption"}
          weight={active ? 800 : 600}
          color={color}
        >
          {tr.nav[destination]}
        </Label>
      </Action>
    );
    return onSelect ? (
      <View key={destination} style={side ? undefined : styles.tab}>
        {item}
      </View>
    ) : (
      <Link key={destination} href={`/${destination}`} asChild>
        {item}
      </Link>
    );
  });
}
export function TabBar({ label = tr.nav.menu, ...props }: NavProps) {
  return (
    <View role="navigation" accessibilityLabel={label} style={styles.tabs}>
      <NavItems {...props} side={false} />
    </View>
  );
}
export function SideNav({
  label = tr.nav.menu,
  appName,
  examLabel,
  ...props
}: NavProps & { appName?: string; examLabel?: string }) {
  return (
    <View role="navigation" accessibilityLabel={label} style={styles.sidebar}>
      <Label variant="wordmark" color={colors.primary} style={styles.wordmark}>
        {appName ?? appConfig.expo.name}
      </Label>
      {examLabel && <Chip tone="butter" label={examLabel} />}
      <View style={styles.links}>
        <NavItems {...props} side />
      </View>
    </View>
  );
}
const styles = StyleSheet.create({
  tabs: {
    alignSelf: "center",
    width: "100%",
    maxWidth: size.column,
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.nav,
    borderTopRightRadius: radius.nav,
    boxShadow: shadow.nav,
    flexDirection: "row",
    gap: space.x4,
    paddingTop: space.x8,
    paddingHorizontal: space.x12,
    paddingBottom: space.x14,
  },
  tab: { flex: 1 },
  tabItem: {
    flex: 1,
    minHeight: size.tabHeight,
    alignItems: "center",
    gap: space.x2,
  },
  iconPill: {
    width: size.tabIconWidth,
    height: size.tabIconHeight,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  active: { backgroundColor: colors.primaryTint },
  sidebar: {
    alignSelf: "stretch",
    width: size.rail,
    backgroundColor: colors.surface,
    paddingVertical: space.x24,
    paddingHorizontal: space.x16,
    gap: space.x20,
  },
  wordmark: { paddingHorizontal: space.x14 },
  links: { gap: space.x4 },
  sideItem: {
    minHeight: size.choice,
    flexDirection: "row",
    justifyContent: "flex-start",
    alignItems: "center",
    gap: space.x12,
    paddingHorizontal: space.x14,
    borderRadius: radius.pill,
  },
});
