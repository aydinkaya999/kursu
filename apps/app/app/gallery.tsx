import { Redirect } from "expo-router";
import { lazy, Suspense } from "react";
const Gallery = __DEV__
  ? lazy(() => import("../src/features/gallery/Gallery"))
  : null;
export default function GalleryRoute() {
  return Gallery ? (
    <Suspense fallback={null}>
      <Gallery />
    </Suspense>
  ) : (
    <Redirect href="/today" />
  );
}
