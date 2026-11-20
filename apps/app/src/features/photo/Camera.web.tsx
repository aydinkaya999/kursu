import { useEffect, useRef, useState } from "react";
import { View } from "react-native";
import { Button } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { radius, space } from "../../theme";
import { Picker, type CaptureProps } from "./Picker";

export function Camera({ disabled, onImage, onError }: CaptureProps) {
  const [active, setActive] = useState(false);
  const [ready, setReady] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    if (!active) return;
    let closed = false;
    let stream: MediaStream | undefined;
    void navigator.mediaDevices
      .getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      })
      .then((media) => {
        if (closed) {
          media.getTracks().forEach((track) => track.stop());
          return;
        }
        stream = media;
        if (video.current) video.current.srcObject = media;
      })
      .catch(() => {
        if (!closed) {
          setActive(false);
          onError(tr.photo.cameraPermission);
        }
      });
    return () => {
      closed = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [active, onError]);
  if (!globalThis.navigator?.mediaDevices?.getUserMedia) {
    return (
      <Picker camera disabled={disabled} onImage={onImage} onError={onError} />
    );
  }
  function stop() {
    setActive(false);
    setReady(false);
  }
  function capture() {
    const frame = video.current;
    if (!frame?.videoWidth || !frame.videoHeight) return;
    const canvas = document.createElement("canvas");
    canvas.width = frame.videoWidth;
    canvas.height = frame.videoHeight;
    const context = canvas.getContext("2d");
    if (context) {
      context.drawImage(frame, 0, 0);
      const data = canvas.toDataURL("image/jpeg", 0.85).split(",")[1];
      if (data) onImage(data);
      else onError(tr.photo.invalid);
    } else onError(tr.photo.invalid);
    stop();
  }
  if (!active)
    return (
      <Button
        disabled={disabled}
        label={tr.photo.take}
        onPress={() => setActive(true)}
      />
    );
  return (
    <View style={{ gap: space.x8 }}>
      <video
        ref={video}
        aria-label={tr.photo.cameraPreview}
        autoPlay
        muted
        playsInline
        onLoadedData={() => setReady(true)}
        style={{ width: "100%", maxHeight: "40vh", borderRadius: radius.task }}
      />
      <Button
        label={tr.photo.take}
        disabled={!ready || disabled}
        onPress={capture}
      />
      <Button label={tr.account.cancel} variant="text" onPress={stop} />
    </View>
  );
}
