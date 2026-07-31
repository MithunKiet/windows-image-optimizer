"""Per-file copy/compress logic."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from cimageoptimizer.core.constants import IMAGE_EXTENSIONS
from cimageoptimizer.core.models import OptimizationSettings
from cimageoptimizer.infrastructure.filesystem import copy_file

JPEG_EXTENSIONS = (".jpg", ".jpeg")


class ImageCompressionService:
    """Copies or compresses a single file from source to destination."""

    def process(self, src_file: Path, dst_file: Path, settings: OptimizationSettings) -> None:
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        extension = src_file.suffix.lower()
        size_mb = src_file.stat().st_size / (1024 * 1024)

        if extension not in IMAGE_EXTENSIONS or size_mb <= settings.max_size_mb:
            copy_file(src_file, dst_file)
            return

        self._compress_image(src_file, dst_file, settings)

    def _compress_image(self, src_file: Path, dst_file: Path, settings: OptimizationSettings) -> None:
        with Image.open(src_file) as img:
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            if not settings.preserve_resolution and img.width > settings.max_width:
                ratio = settings.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((settings.max_width, new_height), Image.LANCZOS)

            extension = src_file.suffix.lower()
            quality = settings.initial_quality

            while quality >= settings.min_quality:
                img.save(
                    dst_file,
                    format="JPEG" if extension in JPEG_EXTENSIONS else None,
                    quality=quality,
                    optimize=True,
                    progressive=True,
                )

                final_size_mb = dst_file.stat().st_size / (1024 * 1024)
                if final_size_mb <= settings.max_size_mb:
                    break

                quality -= settings.quality_step
