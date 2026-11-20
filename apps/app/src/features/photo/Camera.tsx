import { Picker, type CaptureProps } from "./Picker";

export function Camera(props: CaptureProps) {
  return <Picker {...props} camera />;
}
