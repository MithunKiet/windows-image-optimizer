"""Per-file copy/compress logic."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from cimageoptimizer.core.constants import IMAGE_EXTENSIONS, QUALITY_CONTROLLABLE_EXTENSIONS
from cimageoptimizer.core.models import OptimizationSettings
from cimageoptimizer.infrastructure.filesystem import copy_file

JPEG_EXTENSIONS = (".jpg", ".jpeg")


class ImageCompressionService:
    """Copies or compresses a single file from source to destination.

    Returns the path actually written, which is normally dst_file but can
    differ when a lossless format gets converted to .jpg (see
    _compress_lossless).
    """

    def process(self, src_file: Path, dst_file: Path, settings: OptimizationSettings) -> Path:
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        extension = src_file.suffix.lower()
        size_mb = src_file.stat().st_size / (1024 * 1024)

        if extension not in IMAGE_EXTENSIONS or size_mb <= settings.max_size_mb:
            copy_file(src_file, dst_file)
            return dst_file

        return self._compress_image(src_file, dst_file, settings)

    def _compress_image(self, src_file: Path, dst_file: Path, settings: OptimizationSettings) -> Path:
        with Image.open(src_file) as img:
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            if not settings.preserve_resolution and img.width > settings.max_width:
                ratio = settings.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((settings.max_width, new_height), Image.LANCZOS)

            extension = src_file.suffix.lower()
            if extension in QUALITY_CONTROLLABLE_EXTENSIONS:
                self._compress_with_quality_search(img, dst_file, extension, settings)
                return dst_file

            return self._compress_lossless(img, dst_file, settings)

    def _compress_with_quality_search(
        self, img: Image.Image, dst_file: Path, extension: str, settings: OptimizationSettings
    ) -> None:
        """Iteratively lowers quality until under the size target or the
        profile's quality floor is reached. Only meaningful for formats
        where `quality` genuinely affects output size (JPEG, WEBP)."""
        quality = settings.initial_quality

        while quality >= settings.min_quality:
            img.save(
                dst_file,
                format="JPEG" if extension in JPEG_EXTENSIONS else None,
                quality=quality,
                optimize=True,
                progressive=extension in JPEG_EXTENSIONS,
            )

            final_size_mb = dst_file.stat().st_size / (1024 * 1024)
            if final_size_mb <= settings.max_size_mb:
                break

            quality -= settings.quality_step

    def _compress_lossless(self, img: Image.Image, dst_file: Path, settings: OptimizationSettings) -> Path:
        """Single-pass save for formats where `quality` has no effect
        (PNG/BMP/TIFF/etc.). Looping quality here would just re-encode
        identical bytes repeatedly. If the single pass is still over the
        size target and the caller opted in, falls back to a real lossy
        .jpg instead, replacing the lossless output."""
        img.save(dst_file, optimize=True)

        final_size_mb = dst_file.stat().st_size / (1024 * 1024)
        if final_size_mb <= settings.max_size_mb or not settings.convert_to_jpeg_if_oversized:
            return dst_file

        jpeg_dst = dst_file.with_suffix(".jpg")
        self._compress_with_quality_search(img, jpeg_dst, ".jpg", settings)
        dst_file.unlink(missing_ok=True)
        return jpeg_dst
