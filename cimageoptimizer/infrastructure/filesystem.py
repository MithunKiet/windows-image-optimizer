"""Thin filesystem helpers used by the application layer."""

import shutil
from pathlib import Path


def copy_file(src_file: Path, dst_file: Path) -> None:
    """Copies a file, preserving metadata. Caller is responsible for ensuring
    the destination's parent directory already exists."""
    shutil.copy2(src_file, dst_file)
