from cimageoptimizer.application.services.optimization_service import OptimizationService
from cimageoptimizer.core.models import OptimizationSettings


def test_run_processes_an_explicit_file_selection_flattened_into_output(tmp_path, make_image):
    output = tmp_path / "output"
    a = make_image(tmp_path / "folder_one" / "a.jpg")
    b = make_image(tmp_path / "folder_two" / "b.jpg")

    settings = OptimizationSettings(
        source_dir=tmp_path,  # unused when source_files is set, but required
        output_dir=output,
        source_files=(a, b),
    )
    result = OptimizationService().run(settings)

    assert result.total_files == 2
    assert result.failed_count == 0
    assert (output / "a.jpg").exists()
    assert (output / "b.jpg").exists()


def test_for_profile_accepts_source_files():
    from pathlib import Path

    from cimageoptimizer.core.enums import OptimizationProfile

    settings = OptimizationSettings.for_profile(
        OptimizationProfile.RECOMMENDED,
        Path("unused"),
        Path("out"),
        source_files=[Path("a.jpg"), Path("b.jpg")],
    )

    assert settings.source_files == (Path("a.jpg"), Path("b.jpg"))
