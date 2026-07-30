from cimageoptimizer.application.services.optimization_service import OptimizationService
from cimageoptimizer.core.models import OptimizationSettings


def test_run_processes_many_files_concurrently_without_data_races(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    file_count = 40
    for i in range(file_count):
        make_image(source / f"img_{i:03d}.jpg", width=40, height=40)

    service = OptimizationService(max_workers=8)
    result = service.run(OptimizationSettings(source_dir=source, output_dir=output))

    assert result.total_files == file_count
    assert result.failed_count == 0
    assert len(list(output.glob("*.jpg"))) == file_count


def test_run_defaults_to_a_positive_worker_count():
    service = OptimizationService(max_workers=0)
    assert service._max_workers > 0
