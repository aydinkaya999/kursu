import { Link } from "expo-router";
import { View } from "react-native";
import { Action, Label } from "../../components/Core";
import { Icon } from "../../components/Icon";
import { tr } from "../../i18n/tr";
import { colors, radius, space } from "../../theme";

export function PhotoTile({ remaining }: { remaining?: number }) {
  const rights =
    remaining !== undefined ? tr.photo.rights(remaining) : undefined;
  return (
    <Link href="/photo" asChild>
      <Action
        accessibilityRole="link"
        accessibilityLabel={[tr.photo.tile, rights].filter(Boolean).join(". ")}
        style={{
          backgroundColor: colors.rose,
          borderRadius: radius.task,
          padding: space.x12,
          gap: space.x6,
        }}
      >
        <View
          style={{ flexDirection: "row", alignItems: "center", gap: space.x8 }}
        >
          <Icon name="camera" color={colors.roseInk} />
          <Label variant="tileTitle" color={colors.roseInk}>
            {tr.photo.tile}
          </Label>
        </View>
        {rights && (
          <Label variant="caption" color={colors.roseInk}>
            {rights}
          </Label>
        )}
      </Action>
    </Link>
  );
}
