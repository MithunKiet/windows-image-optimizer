"""Orchestrates a full optimization run: discovery, per-file processing, reporting."""

from __future__ import annotations

import logging
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


class OptimizationService:
    """Coordinates discovery and compression services to run a full batch."""

    def __init__(
        self,
        discovery_service: Optional[FileDiscoveryService] = None,
        compression_service: Optional[ImageCompressionService] = None,
    ) -> None:
        self._discovery_service = discovery_service or FileDiscoveryService()
        self._compression_service = compression_service or ImageCompressionService()

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

        log(f"Source: {settings.source_dir}")
        log(f"Output: {settings.output_dir}")
        log("Scanning for files to process...")

        missing_files = self._discovery_service.find_missing_files(
            settings.source_dir, settings.output_dir, settings.images_only
        )
        total_files = len(missing_files)
        log(f"Files found to process: {total_files}")

        result = OptimizationResult(total_files=total_files)

        if total_files == 0:
            log("No new files to optimize.")
            return result

        for index, src_file in enumerate(missing_files):
            if check_cancel_callback and check_cancel_callback():
                log("Optimization cancelled by user.")
                result.cancelled = True
                break

            if progress_callback:
                progress_callback(index, total_files)

            relative_path = src_file.relative_to(settings.source_dir)
            dst_file = settings.output_dir / relative_path

            self._process_one(src_file, dst_file, settings, result)

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

    def _process_one(self, src_file, dst_file, settings: OptimizationSettings, result: OptimizationResult) -> None:
        try:
            self._compression_service.process(src_file, dst_file, settings)
        except Exception as exc:  # noqa: BLE001 - a single bad file must not abort the batch
            logger.exception("Failed to process %s", src_file)
            result.failures.append(FileOutcome(source=src_file, error=str(exc)))
            try:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                copy_file(src_file, dst_file)
            except Exception as copy_error:  # noqa: BLE001
                result.failures.append(FileOutcome(source=src_file, error=f"copy failed: {copy_error}"))
