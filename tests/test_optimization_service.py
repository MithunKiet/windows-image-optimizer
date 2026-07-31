from cimageoptimizer.application.services.optimization_service import OptimizationService
from cimageoptimizer.core.enums import ProcessMode
from cimageoptimizer.core.models import OptimizationSettings


def test_run_processes_all_missing_files(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    (source / "notes.txt").write_text("hi")

    result = OptimizationService().run(OptimizationSettings(source_dir=source, output_dir=output))

    assert result.total_files == 2
    assert result.failed_count == 0
    assert (output / "a.jpg").exists()
    assert (output / "notes.txt").exists()


def test_run_is_incremental(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    make_image(output / "a.jpg")

    result = OptimizationService().run(OptimizationSettings(source_dir=source, output_dir=output))

    assert result.total_files == 0


def test_run_with_overwrite_existing_reprocesses_files(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    make_image(output / "a.jpg")

    settings = OptimizationSettings(source_dir=source, output_dir=output, overwrite_existing=True)
    result = OptimizationService().run(settings)

    assert result.total_files == 1
    assert result.failed_count == 0


def test_run_respects_images_only_mode(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    (source / "notes.txt").write_text("hi")

    settings = OptimizationSettings(source_dir=source, output_dir=output, process_mode=ProcessMode.IMAGES_ONLY)
    result = OptimizationService().run(settings)

    assert result.total_files == 1
    assert (output / "a.jpg").exists()
    assert not (output / "notes.txt").exists()


def test_run_honors_cancel_callback(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    make_image(source / "b.jpg")

    result = OptimizationService().run(
        OptimizationSettings(source_dir=source, output_dir=output),
        check_cancel_callback=lambda: True,
    )

    assert result.cancelled is True


def test_run_reflects_jpeg_conversion_in_the_outcome(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "big.png", width=800, height=600, noisy=True, quality=100)

    settings = OptimizationSettings(
        source_dir=source,
        output_dir=output,
        max_size_mb=0.001,
        min_quality=10,
        quality_step=10,
        convert_to_jpeg_if_oversized=True,
    )
    result = OptimizationService().run(settings)

    assert result.total_files == 1
    assert result.failed_count == 0
    outcome = result.outcomes[0]
    assert outcome.destination == output / "big.jpg"
    assert not (output / "big.png").exists()
    assert (output / "big.jpg").exists()


def test_run_writes_failed_log_and_falls_back_to_copy(tmp_path, make_image, monkeypatch):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")

    service = OptimizationService()

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(service._compression_service, "process", boom)

    result = service.run(OptimizationSettings(source_dir=source, output_dir=output))

    assert result.failed_count == 1
    assert (output / "missing_failed_log.txt").exists()
    assert (output / "a.jpg").exists()
