"""Shared constants for the optimization pipeline."""

from cimageoptimizer.core.enums import OptimizationProfile

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"})

# Formats where Pillow's `quality` parameter genuinely produces smaller
# output at lower values. PNG/BMP/TIFF are lossless in Pillow's plain
# save() - passing `quality` to them is silently ignored, so iterating it
# in a loop just re-encodes the same bytes repeatedly for no benefit.
QUALITY_CONTROLLABLE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".webp"})

DEFAULT_MAX_SIZE_MB = 1.0
DEFAULT_INITIAL_QUALITY = 85
DEFAULT_MIN_QUALITY = 45
DEFAULT_MAX_WIDTH = 1920
DEFAULT_QUALITY_STEP = 5

FAILED_LOG_FILENAME = "missing_failed_log.txt"

# Recommended matches the tool's original (and only) behavior, so switching
# profiles is purely additive - existing users see no change unless they
# opt into Safe or Advanced.
PROFILE_PRESETS = {
    OptimizationProfile.SAFE: {
        "max_size_mb": 2.0,
        "initial_quality": 90,
        "min_quality": 70,
        "max_width": 2560,
        "quality_step": 5,
    },
    OptimizationProfile.RECOMMENDED: {
        "max_size_mb": DEFAULT_MAX_SIZE_MB,
        "initial_quality": DEFAULT_INITIAL_QUALITY,
        "min_quality": DEFAULT_MIN_QUALITY,
        "max_width": DEFAULT_MAX_WIDTH,
        "quality_step": DEFAULT_QUALITY_STEP,
    },
    OptimizationProfile.ADVANCED: {
        "max_size_mb": 0.5,
        "initial_quality": 80,
        "min_quality": 30,
        "max_width": 1600,
        "quality_step": 5,
    },
}
