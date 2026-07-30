"""Finds work that a given optimization run needs to do."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from cimageoptimizer.core.constants import IMAGE_EXTENSIONS


class FileDiscoveryService:
    """Finds files present in the source tree but missing from the output tree.

    A file is considered "missing" purely by relative path existing under
    output_dir; this makes repeated runs incremental (only new files are
    processed), at the cost of not re-processing files whose content changed
    but whose relative path already exists in the output tree.
    """

    def find_missing_files(self, source_dir: Path, output_dir: Path, images_only: bool) -> list[Path]:
        return list(self._iter_missing_files(source_dir, output_dir, images_only))

    def _iter_missing_files(self, source_dir: Path, output_dir: Path, images_only: bool) -> Iterator[Path]:
        for src_file in source_dir.rglob("*"):
            if not src_file.is_file():
                continue

            if images_only and src_file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            relative_path = src_file.relative_to(source_dir)
            if not (output_dir / relative_path).exists():
                yield src_file
