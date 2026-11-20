import * as ImagePicker from "expo-image-picker";
import { useRef, useState } from "react";
import { Platform } from "react-native";
import { Button } from "../../components/Core";
import { tr } from "../../i18n/tr";

export type CaptureProps = {
  disabled: boolean;
  onImage: (image: string) => void;
  onError: (message: string) => void;
};

export function selectedImage(result: ImagePicker.ImagePickerResult) {
  if (result.canceled) return null;
  const asset = result.assets[0];
  if (Platform.OS === "web" && asset?.uri.startsWith("blob:"))
    URL.revokeObjectURL(asset.uri);
  if (!asset?.base64) throw new Error(tr.photo.invalid);
  return asset.base64;
}

export function Picker({
  camera = false,
  disabled,
  onImage,
  onError,
}: CaptureProps & { camera?: boolean }) {
  const [waiting, setWaiting] = useState(false);
  const open = useRef(false);
  async function pick() {
    if (open.current) return;
    open.current = true;
    setWaiting(true);
    try {
      if (
        camera &&
        Platform.OS !== "web" &&
        !(await ImagePicker.requestCameraPermissionsAsync()).granted
      ) {
        onError(tr.photo.cameraPermission);
        return;
      }
      const options: ImagePicker.ImagePickerOptions = {
        mediaTypes: ["images"],
        base64: true,
        quality: 0.85,
        exif: false,
        preferredAssetRepresentationMode:
          ImagePicker.UIImagePickerPreferredAssetRepresentationMode.Compatible,
      };
      const result = camera
        ? await ImagePicker.launchCameraAsync(options)
        : await ImagePicker.launchImageLibraryAsync(options);
      const image = selectedImage(result);
      if (image) onImage(image);
    } catch {
      onError(tr.photo.invalid);
    } finally {
      open.current = false;
      setWaiting(false);
    }
  }
  return (
    <Button
      label={camera ? tr.photo.take : tr.photo.upload}
      variant={camera ? "primary" : "secondary"}
      disabled={disabled || waiting}
      onPress={() => void pick()}
    />
  );
}
