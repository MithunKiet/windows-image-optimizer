import csv
import json
from pathlib import Path

from cimageoptimizer.application.services.report_service import ReportService
from cimageoptimizer.core.models import FileOutcome, OptimizationResult


def _sample_result() -> OptimizationResult:
    return OptimizationResult(
        total_files=2,
        outcomes=[
            FileOutcome(
                source=Path("src/a.jpg"),
                destination=Path("out/a.jpg"),
                original_size_bytes=2_000_000,
                final_size_bytes=800_000,
            ),
            FileOutcome(source=Path("src/b.jpg"), error="boom"),
        ],
    )


def test_export_json_writes_summary_and_per_file_rows(tmp_path):
    result = _sample_result()
    path = tmp_path / "report.json"

    ReportService().export_json(result, path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["total_files"] == 2
    assert payload["failed_count"] == 1
    assert payload["bytes_saved"] == 1_200_000
    assert len(payload["files"]) == 2
    assert payload["files"][1]["error"] == "boom"


def test_export_csv_writes_a_row_per_file(tmp_path):
    result = _sample_result()
    path = tmp_path / "report.csv"

    ReportService().export_csv(result, path)

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["source", "destination", "original_size_bytes", "final_size_bytes", "error"]
    assert len(rows) == 3
    assert rows[2][-1] == "boom"
