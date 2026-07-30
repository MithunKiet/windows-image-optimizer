"""Enumerations shared across the application."""

from enum import Enum


class ProcessMode(str, Enum):
    """Which files a run should touch."""

    ALL_FILES = "all_files"
    IMAGES_ONLY = "images_only"


class OptimizationProfile(str, Enum):
    """Preset compression aggressiveness, trading output size against quality."""

    SAFE = "safe"
    RECOMMENDED = "recommended"
    ADVANCED = "advanced"
