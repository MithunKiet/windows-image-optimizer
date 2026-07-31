"""Core data structures shared between the application and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

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
    # When set, the run processes exactly these files instead of walking
    # source_dir. Files are written flat into output_dir (by filename),
    # since an explicit selection may span unrelated directories with no
    # common structure worth preserving. source_dir is still required and
    # used for logging/display, but is not used for path resolution in
    # this mode.
    source_files: Optional[tuple[Path, ...]] = None
    # When True, images are never resized regardless of max_width - only
    # quality/compression is used to reduce file size.
    preserve_resolution: bool = False
    # When True, a file is reprocessed even if a same-named file already
    # exists at its destination (normally such files are skipped, which is
    # what makes reruns incremental).
    overwrite_existing: bool = False

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
        source_files: Optional[Sequence[Path]] = None,
        preserve_resolution: bool = False,
        overwrite_existing: bool = False,
    ) -> "OptimizationSettings":
        """Builds settings from one of the Safe/Recommended/Advanced presets."""
        preset = PROFILE_PRESETS[profile]
        return cls(
            source_dir=source_dir,
            output_dir=output_dir,
            process_mode=process_mode,
            source_files=tuple(source_files) if source_files is not None else None,
            preserve_resolution=preserve_resolution,
            overwrite_existing=overwrite_existing,
            **preset,
        )


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
