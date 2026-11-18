import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import { useState } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { FontContext } from "../src/theme";
import { fonts } from "../src/theme/fonts";

export default function RootLayout() {
  const [client] = useState(() => new QueryClient());
  const [fontsLoaded] = useFonts(fonts);
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={client}>
        <FontContext.Provider value={fontsLoaded}>
          <Stack screenOptions={{ headerShown: false, animation: "none" }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="(tabs)" />
            <Stack.Protected guard={__DEV__}>
              <Stack.Screen name="gallery" />
            </Stack.Protected>
          </Stack>
        </FontContext.Provider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
