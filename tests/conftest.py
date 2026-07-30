"""Shared pytest fixtures."""

import random
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def make_image():
    """Factory fixture that writes a JPEG to `path` and returns it.

    Set noisy=True to produce content that doesn't compress trivially,
    needed for tests that exercise the quality-search compression path.
    """

    def _make(path: Path, width: int = 100, height: int = 100, noisy: bool = False, quality: int = 95) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (width, height))
        if noisy:
            random.seed(0)
            img.putdata(
                [
                    (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    for _ in range(width * height)
                ]
            )
        img.save(path, quality=quality)
        return path

    return _make
