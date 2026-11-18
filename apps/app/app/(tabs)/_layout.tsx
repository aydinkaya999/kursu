import { Slot, usePathname } from "expo-router";
import { Platform, StyleSheet, View, useWindowDimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { destinations, SideNav, TabBar } from "../../src/components/Navigation";
import { colors, size } from "../../src/theme";

export default function NavigationLayout() {
  const wide =
    useWindowDimensions().width >= size.wide && Platform.OS === "web";
  const path = usePathname().split("/")[1] ?? "";
  const current =
    destinations.find((destination) => destination === path) ?? "today";
  return (
    <SafeAreaView style={[styles.shell, wide && styles.wide]}>
      {wide && <SideNav current={current} />}
      <View style={styles.page}>
        <Slot />
      </View>
      {!wide && <TabBar current={current} />}
    </SafeAreaView>
  );
}
const styles = StyleSheet.create({
  shell: { flex: 1, backgroundColor: colors.ground },
  wide: { flexDirection: "row" },
  page: { flex: 1, minWidth: 0 },
});
