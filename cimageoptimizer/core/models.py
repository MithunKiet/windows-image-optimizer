"""Core data structures shared between the application and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from cimageoptimizer.core.constants import (
    DEFAULT_INITIAL_QUALITY,
    DEFAULT_MAX_SIZE_MB,
    DEFAULT_MAX_WIDTH,
    DEFAULT_MIN_QUALITY,
    DEFAULT_QUALITY_STEP,
    PROFILE_PRESETS,
)
from cimageoptimizer.core.enums import OptimizationProfile, ProcessMode

ProgressCallback = Callable[[int, int], None]
LogCallback = Callable[[str], None]
CancelCallback = Callable[[], bool]


@dataclass(frozen=True)
class OptimizationSettings:
    """Parameters for a single optimization run."""

    source_dir: Path
    output_dir: Path
    process_mode: ProcessMode = ProcessMode.ALL_FILES
    max_size_mb: float = DEFAULT_MAX_SIZE_MB
    initial_quality: int = DEFAULT_INITIAL_QUALITY
    min_quality: int = DEFAULT_MIN_QUALITY
    max_width: int = DEFAULT_MAX_WIDTH
    quality_step: int = DEFAULT_QUALITY_STEP

    @property
    def images_only(self) -> bool:
        return self.process_mode is ProcessMode.IMAGES_ONLY

    @classmethod
    def for_profile(
        cls,
        profile: OptimizationProfile,
        source_dir: Path,
        output_dir: Path,
        process_mode: ProcessMode = ProcessMode.ALL_FILES,
    ) -> "OptimizationSettings":
        """Builds settings from one of the Safe/Recommended/Advanced presets."""
        preset = PROFILE_PRESETS[profile]
        return cls(source_dir=source_dir, output_dir=output_dir, process_mode=process_mode, **preset)


@dataclass
class FileOutcome:
    """The result of attempting to process a single file."""

    source: Path
    destination: Optional[Path] = None
    original_size_bytes: Optional[int] = None
    final_size_bytes: Optional[int] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass
class OptimizationResult:
    """Summary of a completed (or cancelled) optimization run."""

    total_files: int
    outcomes: list[FileOutcome] = field(default_factory=list)
    cancelled: bool = False

    @property
    def failures(self) -> list[FileOutcome]:
        return [outcome for outcome in self.outcomes if not outcome.succeeded]

    @property
    def failed_count(self) -> int:
        return len(self.failures)

    @property
    def bytes_saved(self) -> int:
        return sum(
            outcome.original_size_bytes - outcome.final_size_bytes
            for outcome in self.outcomes
            if outcome.succeeded
            and outcome.original_size_bytes is not None
            and outcome.final_size_bytes is not None
        )
