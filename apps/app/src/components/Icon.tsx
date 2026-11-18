import Svg, { Circle, Path, Rect } from "react-native-svg";
import { colors } from "../theme";
const artwork = {
  check: <Path d="M5 12.5l4.5 4.5L19 7.5" />,
  cross: <Path d="M6 6l12 12M18 6L6 18" />,
  back: <Path d="M19 12H5M11 6l-6 6 6 6" />,
  chevron: <Path d="M9 6l6 6-6 6" />,
  calendar: (
    <>
      <Rect x={3.5} y={5} width={17} height={15} rx={3} />
      <Path d="M3.5 10h17M8 3v4M16 3v4" />
    </>
  ),
  book: (
    <Path d="M12 7c-2-1.5-4.5-2-8-2v13c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2V5c-3.5 0-6 .5-8 2z M12 7v13" />
  ),
  stopwatch: (
    <>
      <Circle cx={12} cy={13.5} r={7.5} />
      <Path d="M12 9.5v4l2.5 2M9.5 3h5" />
    </>
  ),
  chart: <Path d="M4 19.5h16M6.5 15.5l4-4.5 3 3 4.5-6.5" />,
  notebook: (
    <>
      <Rect x={6} y={3.5} width={12} height={17} rx={2} />
      <Path d="M9.5 8h5M9.5 12h5M9.5 16h3" />
    </>
  ),
  pencil: <Path d="M4 20h4L19 9l-4-4L4 16v4z M13.5 6.5l4 4" />,
  camera: (
    <>
      <Path d="M4 8.5h3l1.5-2.5h7L17 8.5h3v10H4z" />
      <Circle cx={12} cy={13} r={3.5} />
    </>
  ),
  flame: (
    <Path d="M12 3c.6 3.2 4.5 5 4.5 9.8a4.5 4.5 0 0 1-9 0c0-1.9.9-3.2 2-4.3.2 1.3.9 2.1 1.6 2.4C10.9 8.8 11.1 5.9 12 3z" />
  ),
  flag: <Path d="M6 21V4h11l-2 4 2 4H6" />,
  bookmark: <Path d="M7 4h10v16l-5-3.5L7 20z" />,
  info: (
    <>
      <Circle cx={12} cy={12} r={8.5} />
      <Path d="M12 11v5M12 8h.01" />
    </>
  ),
  lightbulb: (
    <Path d="M9 18h6M10 21h4 M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z" />
  ),
  medal: (
    <>
      <Circle cx={12} cy={9} r={5} />
      <Path d="M9 13.5L7.5 21l4.5-2.5 4.5 2.5L15 13.5" />
    </>
  ),
  trophy: (
    <Path d="M8 4h8v5a4 4 0 0 1-8 0z M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7" />
  ),
} as const;
export type IconName = keyof typeof artwork;
export function Icon({
  name,
  size = 20,
  color = colors.ink,
}: {
  name: IconName;
  size?: number;
  color?: string;
}) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={name === "check" || name === "cross" ? 2.5 : 2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      focusable={false}
    >
      {artwork[name]}
    </Svg>
  );
}
