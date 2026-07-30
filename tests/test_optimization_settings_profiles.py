from pathlib import Path

from cimageoptimizer.core.constants import (
    DEFAULT_INITIAL_QUALITY,
    DEFAULT_MAX_SIZE_MB,
    DEFAULT_MAX_WIDTH,
    DEFAULT_MIN_QUALITY,
)
from cimageoptimizer.core.enums import OptimizationProfile
from cimageoptimizer.core.models import OptimizationSettings


def test_recommended_profile_matches_original_hardcoded_defaults():
    settings = OptimizationSettings.for_profile(OptimizationProfile.RECOMMENDED, Path("src"), Path("out"))

    assert settings.max_size_mb == DEFAULT_MAX_SIZE_MB
    assert settings.initial_quality == DEFAULT_INITIAL_QUALITY
    assert settings.min_quality == DEFAULT_MIN_QUALITY
    assert settings.max_width == DEFAULT_MAX_WIDTH


def test_safe_profile_is_less_aggressive_than_advanced():
    safe = OptimizationSettings.for_profile(OptimizationProfile.SAFE, Path("src"), Path("out"))
    advanced = OptimizationSettings.for_profile(OptimizationProfile.ADVANCED, Path("src"), Path("out"))

    assert safe.max_size_mb > advanced.max_size_mb
    assert safe.min_quality > advanced.min_quality
    assert safe.max_width > advanced.max_width
