"""Exports an OptimizationResult as a JSON or CSV report."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from cimageoptimizer.core.models import OptimizationResult


class ReportService:
    """Writes a completed run's results to disk for later review."""

    def export_json(self, result: OptimizationResult, path: Path) -> None:
        payload = {
            "total_files": result.total_files,
            "failed_count": result.failed_count,
            "cancelled": result.cancelled,
            "bytes_saved": result.bytes_saved,
            "files": [
                {
                    "source": str(outcome.source),
                    "destination": str(outcome.destination) if outcome.destination else None,
                    "original_size_bytes": outcome.original_size_bytes,
                    "final_size_bytes": outcome.final_size_bytes,
                    "error": outcome.error,
                }
                for outcome in result.outcomes
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def export_csv(self, result: OptimizationResult, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["source", "destination", "original_size_bytes", "final_size_bytes", "error"])
            for outcome in result.outcomes:
                writer.writerow(
                    [
                        outcome.source,
                        outcome.destination or "",
                        outcome.original_size_bytes if outcome.original_size_bytes is not None else "",
                        outcome.final_size_bytes if outcome.final_size_bytes is not None else "",
                        outcome.error or "",
                    ]
                )
