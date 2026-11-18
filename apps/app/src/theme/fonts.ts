import { PlusJakartaSans_400Regular } from "@expo-google-fonts/plus-jakarta-sans/400Regular";
import { PlusJakartaSans_500Medium } from "@expo-google-fonts/plus-jakarta-sans/500Medium";
import { PlusJakartaSans_600SemiBold } from "@expo-google-fonts/plus-jakarta-sans/600SemiBold";
import { PlusJakartaSans_700Bold } from "@expo-google-fonts/plus-jakarta-sans/700Bold";
import { PlusJakartaSans_800ExtraBold } from "@expo-google-fonts/plus-jakarta-sans/800ExtraBold";
import { families } from "./typography";
export const fonts = {
  [families[400]]: PlusJakartaSans_400Regular,
  [families[500]]: PlusJakartaSans_500Medium,
  [families[600]]: PlusJakartaSans_600SemiBold,
  [families[700]]: PlusJakartaSans_700Bold,
  [families[800]]: PlusJakartaSans_800ExtraBold,
};
