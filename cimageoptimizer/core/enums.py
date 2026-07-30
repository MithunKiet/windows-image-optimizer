"""Enumerations shared across the application."""

from enum import Enum


class ProcessMode(str, Enum):
    """Which files a run should touch."""

    ALL_FILES = "all_files"
    IMAGES_ONLY = "images_only"
