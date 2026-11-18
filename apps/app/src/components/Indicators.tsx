import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import {
  colors,
  radius,
  shadow,
  size,
  space,
  tones,
  type Tone,
} from "../theme";
import { Label } from "./Core";
import { Icon, type IconName } from "./Icon";
type BadgeProps = { label: string; tone?: Tone; style?: StyleProp<ViewStyle> };
function Badge({
  label,
  tone,
  small,
  style,
}: BadgeProps & { tone: Tone; small: boolean }) {
  const [backgroundColor, color] = tones[tone];
  return (
    <View
      style={[
        styles.badge,
        small ? styles.chip : styles.pill,
        { backgroundColor },
        tone === "surface" && styles.raised,
        style,
      ]}
    >
      <Label variant={small ? "caption" : "meta"} weight={800} color={color}>
        {label}
      </Label>
    </View>
  );
}
export const Pill = ({ tone = "primary", ...props }: BadgeProps) => (
  <Badge {...props} tone={tone} small={false} />
);
export const Chip = ({ tone = "surface", ...props }: BadgeProps) => (
  <Badge {...props} tone={tone} small />
);
const tiles = {
  small: [size.tileSmall, radius.small, 16],
  medium: [size.tileMedium, radius.compact, 18],
  large: [size.tileLarge, radius.field, 22],
} as const;
export function IconTile({
  name,
  tone = "primary",
  scale = "large",
}: {
  name: IconName;
  tone?: Tone;
  scale?: keyof typeof tiles;
}) {
  const [width, borderRadius, iconSize] = tiles[scale];
  return (
    <View
      style={[
        styles.tile,
        { width, height: width, borderRadius, backgroundColor: tones[tone][0] },
      ]}
    >
      <Icon name={name} size={iconSize} color={tones[tone][1]} />
    </View>
  );
}
export function InfoBox({
  label,
  tone = "aqua",
  icon,
}: {
  label: string;
  tone?: Tone;
  icon?: IconName;
}) {
  return (
    <View style={[styles.info, { backgroundColor: tones[tone][0] }]}>
      {icon && <Icon name={icon} size={18} color={tones[tone][1]} />}
      <Label variant="meta" weight={600} color={tones[tone][1]}>
        {label}
      </Label>
    </View>
  );
}
type ProgressVariant = "ground" | "surface" | "primary" | "mock";
const bars = {
  ground: [size.progress, colors.track, colors.primary],
  surface: [size.progress, colors.primaryTint, colors.primary],
  primary: [size.primaryProgress, colors.primaryTrack, colors.onPrimary],
  mock: [size.segment, colors.track, colors.primary],
} as const;
export function ProgressBar({
  value,
  max = 100,
  label,
  variant = "ground",
}: {
  value: number;
  max?: number;
  label: string;
  variant?: ProgressVariant;
}) {
  const [height, backgroundColor, fill] = bars[variant];
  const limit = Math.max(0, max),
    now = Math.min(limit, Math.max(0, value));
  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={label}
      aria-valuemin={0}
      aria-valuemax={limit}
      aria-valuenow={now}
      style={[styles.bar, { height, backgroundColor }]}
    >
      <View
        style={{
          height,
          width: ((limit ? (now / limit) * 100 : 0) + "%") as `${number}%`,
          backgroundColor: fill,
        }}
      />
    </View>
  );
}
export function SegmentedProgress({
  total,
  done,
  label,
}: {
  total: number;
  done: number;
  label: string;
}) {
  const count = Math.max(0, Math.floor(total)),
    filled = Math.min(count, Math.max(0, Math.floor(done)));
  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={label}
      aria-valuemin={0}
      aria-valuemax={count}
      aria-valuenow={filled}
      style={styles.segments}
    >
      {Array.from({ length: count }, (_, index) => (
        <View
          key={index}
          style={[
            styles.segment,
            { backgroundColor: index < filled ? colors.primary : colors.track },
          ]}
        />
      ))}
    </View>
  );
}
const styles = StyleSheet.create({
  badge: { alignSelf: "flex-start", borderRadius: radius.pill },
  chip: { paddingHorizontal: space.x10, paddingVertical: space.x4 },
  pill: { paddingHorizontal: space.x12, paddingVertical: space.x8 },
  raised: { boxShadow: shadow.control },
  tile: { alignItems: "center", justifyContent: "center", flexShrink: 0 },
  info: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.x8,
    paddingVertical: space.x10,
    paddingHorizontal: space.x14,
    borderRadius: radius.field,
  },
  bar: { overflow: "hidden", borderRadius: radius.pill },
  segments: { flexDirection: "row", gap: space.x6 },
  segment: { flex: 1, height: size.segment, borderRadius: radius.pill },
});
