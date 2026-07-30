from pathlib import Path

from cimageoptimizer.core.models import FileOutcome, OptimizationResult


def test_failures_property_filters_out_successes():
    result = OptimizationResult(
        total_files=2,
        outcomes=[
            FileOutcome(source=Path("a.jpg")),
            FileOutcome(source=Path("b.jpg"), error="broke"),
        ],
    )

    assert result.failed_count == 1
    assert result.failures[0].source == Path("b.jpg")


def test_bytes_saved_only_counts_successful_outcomes_with_known_sizes():
    result = OptimizationResult(
        total_files=2,
        outcomes=[
            FileOutcome(source=Path("a.jpg"), original_size_bytes=1000, final_size_bytes=400),
            FileOutcome(source=Path("b.jpg"), error="broke", original_size_bytes=1000),
        ],
    )

    assert result.bytes_saved == 600
