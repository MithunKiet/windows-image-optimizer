"""Orchestrates a full optimization run: discovery, per-file processing, reporting."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Optional

from cimageoptimizer.application.services.compression_service import ImageCompressionService
from cimageoptimizer.application.services.discovery_service import FileDiscoveryService
from cimageoptimizer.core.constants import FAILED_LOG_FILENAME
from cimageoptimizer.core.models import (
    CancelCallback,
    FileOutcome,
    LogCallback,
    OptimizationResult,
    OptimizationSettings,
    ProgressCallback,
)
from cimageoptimizer.infrastructure.filesystem import copy_file

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKERS = min(8, (os.cpu_count() or 4))


class OptimizationService:
    """Coordinates discovery and compression services to run a full batch.

    Files are processed concurrently via a thread pool: each file is an
    independent read/transform/write, so there is no shared mutable state
    between them (result aggregation is the only shared state, and it is
    protected by a lock).
    """

    def __init__(
        self,
        discovery_service: Optional[FileDiscoveryService] = None,
        compression_service: Optional[ImageCompressionService] = None,
        max_workers: Optional[int] = None,
    ) -> None:
        self._discovery_service = discovery_service or FileDiscoveryService()
        self._compression_service = compression_service or ImageCompressionService()
        self._max_workers = max_workers if max_workers and max_workers > 0 else DEFAULT_MAX_WORKERS

    def run(
        self,
        settings: OptimizationSettings,
        progress_callback: Optional[ProgressCallback] = None,
        log_callback: Optional[LogCallback] = None,
        check_cancel_callback: Optional[CancelCallback] = None,
    ) -> OptimizationResult:
        def log(message: str) -> None:
            logger.info(message)
            if log_callback:
                log_callback(message)

        if settings.source_files is not None:
            log(f"Source: {len(settings.source_files)} individual file(s) selected")
        else:
            log(f"Source: {settings.source_dir}")
        log(f"Output: {settings.output_dir}")
        log("Scanning for files to process...")

        if settings.source_files is not None:
            missing_files = self._discovery_service.find_missing_from_files(
                settings.source_files,
                settings.output_dir,
                settings.images_only,
                settings.overwrite_existing,
            )
        else:
            missing_files = self._discovery_service.find_missing_files(
                settings.source_dir,
                settings.output_dir,
                settings.images_only,
                settings.overwrite_existing,
            )
        total_files = len(missing_files)
        log(f"Files found to process: {total_files}")

        result = OptimizationResult(total_files=total_files)

        if total_files == 0:
            log("No new files to optimize.")
            return result

        result_lock = Lock()
        progress_lock = Lock()
        completed_count = 0
        cancelled = False

        def is_cancelled() -> bool:
            nonlocal cancelled
            if not cancelled and check_cancel_callback and check_cancel_callback():
                cancelled = True
            return cancelled

        def worker(src_file: Path) -> None:
            nonlocal completed_count
            if not is_cancelled():
                dst_file = self._destination_for(src_file, settings)
                self._process_one(src_file, dst_file, settings, result, result_lock)

            with progress_lock:
                completed_count += 1
                current = completed_count
            if progress_callback:
                progress_callback(current, total_files)

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # map() blocks until every submission has run; cancellation stops
            # tasks that haven't started yet, in-flight ones finish normally.
            list(executor.map(worker, missing_files))

        if is_cancelled():
            log("Optimization cancelled by user.")
            result.cancelled = True

        if progress_callback:
            progress_callback(total_files, total_files)

        if result.failures:
            log_file = settings.output_dir / FAILED_LOG_FILENAME
            log_file.write_text(
                "\n".join(f"{failure.source} | {failure.error}" for failure in result.failures),
                encoding="utf-8",
            )
            log(f"Failed log saved: {log_file}")

        log("Done. Missing files optimized/copied.")
        return result

    def _destination_for(self, src_file: Path, settings: OptimizationSettings) -> Path:
        if settings.source_files is not None:
            return settings.output_dir / src_file.name
        return settings.output_dir / src_file.relative_to(settings.source_dir)

    def _process_one(
        self,
        src_file: Path,
        dst_file: Path,
        settings: OptimizationSettings,
        result: OptimizationResult,
        result_lock: Lock,
    ) -> None:
        original_size = src_file.stat().st_size
        try:
            self._compression_service.process(src_file, dst_file, settings)
            outcome = FileOutcome(
                source=src_file,
                destination=dst_file,
                original_size_bytes=original_size,
                final_size_bytes=dst_file.stat().st_size,
            )
        except Exception as exc:  # noqa: BLE001 - a single bad file must not abort the batch
            logger.exception("Failed to process %s", src_file)
            outcome = FileOutcome(source=src_file, original_size_bytes=original_size, error=str(exc))
            try:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                copy_file(src_file, dst_file)
            except Exception as copy_error:  # noqa: BLE001
                outcome.error = f"{outcome.error} | copy failed: {copy_error}"

        with result_lock:
            result.outcomes.append(outcome)
