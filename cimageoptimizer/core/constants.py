"""Shared constants for the optimization pipeline."""

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"})

DEFAULT_MAX_SIZE_MB = 1.0
DEFAULT_INITIAL_QUALITY = 85
DEFAULT_MIN_QUALITY = 45
DEFAULT_MAX_WIDTH = 1920
DEFAULT_QUALITY_STEP = 5

FAILED_LOG_FILENAME = "missing_failed_log.txt"
