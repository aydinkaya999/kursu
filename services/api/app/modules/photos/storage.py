import base64
import os
from io import BytesIO
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageOps

from app.core.http import ApiError
from app.modules.photos.schemas import MAX_BYTES


def normalize(encoded: str) -> bytes:
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_BYTES:
            raise ValueError("image exceeds byte limit")
        with Image.open(BytesIO(raw), formats=("JPEG", "PNG", "WEBP")) as image:
            if image.width * image.height > 32_000_000 or getattr(
                image, "is_animated", False
            ):
                raise ValueError("image exceeds pixel limit or is animated")
            image.thumbnail((1800, 1800))
            oriented = ImageOps.exif_transpose(image)
            if oriented.has_transparency_data:
                rgba = oriented.convert("RGBA")
                pixels = Image.new("RGB", oriented.size, "white")
                pixels.paste(rgba, mask=rgba.getchannel("A"))
            else:
                pixels = oriented.convert("RGB")
            pixels.info.clear()
            out = BytesIO()
            pixels.save(out, format="JPEG", quality=85)
            return out.getvalue()
    except (
        ValueError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
    ) as exc:
        raise ApiError(422, "invalid_photo", "Invalid or oversized still image") from exc


def preview(jpeg: bytes) -> str:
    with Image.open(BytesIO(jpeg)) as image:
        image.thumbnail((420, 420))
        out = BytesIO()
        image.save(out, format="JPEG", quality=75)
        return base64.b64encode(out.getvalue()).decode("ascii")


class PhotoStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, photo: UUID) -> Path:
        return self.root / f"{photo}.jpg"

    def save(self, photo: UUID, jpeg: bytes) -> None:
        self.root.mkdir(mode=0o700, exist_ok=True, parents=True)
        path = self.path(photo)
        # A random server ID and exclusive creation keep concurrent files disjoint.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(jpeg)

    def remove(self, photo: UUID) -> None:
        self.path(photo).unlink(missing_ok=True)

    def ids(self) -> list[UUID]:
        photos = []
        for path in self.root.glob("*.jpg"):
            try:
                photos.append(UUID(path.stem))
            except ValueError:
                continue
        return photos
