from PIL import Image

from cimageoptimizer.application.services.compression_service import ImageCompressionService
from cimageoptimizer.core.models import OptimizationSettings


def _settings(tmp_path, **overrides):
    defaults = dict(source_dir=tmp_path, output_dir=tmp_path)
    defaults.update(overrides)
    return OptimizationSettings(**defaults)


def test_small_image_is_copied_unchanged(tmp_path, make_image):
    src = make_image(tmp_path / "src.jpg", width=50, height=50)
    dst = tmp_path / "out" / "src.jpg"

    ImageCompressionService().process(src, dst, _settings(tmp_path, max_size_mb=1))

    assert dst.read_bytes() == src.read_bytes()


def test_non_image_file_is_copied(tmp_path):
    src = tmp_path / "data.bin"
    src.write_bytes(b"\x00" * 10)
    dst = tmp_path / "out" / "data.bin"

    ImageCompressionService().process(src, dst, _settings(tmp_path))

    assert dst.read_bytes() == src.read_bytes()


def test_large_image_is_resized_and_shrunk(tmp_path, make_image):
    src = make_image(tmp_path / "big.jpg", width=3000, height=2000, noisy=True, quality=100)
    dst = tmp_path / "out" / "big.jpg"
    settings = _settings(tmp_path, max_size_mb=1, max_width=1920, initial_quality=85, min_quality=45, quality_step=5)

    ImageCompressionService().process(src, dst, settings)

    assert dst.exists()
    with Image.open(dst) as out_img:
        assert out_img.width <= 1920
    assert dst.stat().st_size < src.stat().st_size


def test_preserve_resolution_skips_resizing(tmp_path, make_image):
    src = make_image(tmp_path / "big.jpg", width=3000, height=2000, noisy=True, quality=100)
    dst = tmp_path / "out" / "big.jpg"
    settings = _settings(
        tmp_path,
        max_size_mb=1,
        max_width=1920,
        initial_quality=85,
        min_quality=45,
        quality_step=5,
        preserve_resolution=True,
    )

    ImageCompressionService().process(src, dst, settings)

    assert dst.exists()
    with Image.open(dst) as out_img:
        assert out_img.width == 3000
        assert out_img.height == 2000
    # Still compressed via quality, even though dimensions are unchanged.
    assert dst.stat().st_size < src.stat().st_size


def test_png_is_compressed_in_a_single_pass_not_a_quality_loop(tmp_path, make_image, monkeypatch):
    # PNG ignores `quality` entirely in Pillow, so looping it (as JPEG does)
    # would just re-encode identical bytes repeatedly for no benefit.
    src = make_image(tmp_path / "big.png", width=800, height=600, noisy=True, quality=100)
    dst = tmp_path / "out" / "big.png"
    # A target this small would force many retries if quality mattered here.
    settings = _settings(tmp_path, max_size_mb=0.001, initial_quality=90, min_quality=10, quality_step=5)

    save_calls = []
    original_save = Image.Image.save

    def counting_save(self, *args, **kwargs):
        save_calls.append(kwargs)
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Image.Image, "save", counting_save)

    actual_dst = ImageCompressionService().process(src, dst, settings)

    assert len(save_calls) == 1
    assert actual_dst == dst
    assert dst.exists()


def test_oversized_png_stays_png_without_conversion_opt_in(tmp_path, make_image):
    src = make_image(tmp_path / "big.png", width=800, height=600, noisy=True, quality=100)
    dst = tmp_path / "out" / "big.png"
    settings = _settings(tmp_path, max_size_mb=0.001, convert_to_jpeg_if_oversized=False)

    actual_dst = ImageCompressionService().process(src, dst, settings)

    assert actual_dst == dst
    assert dst.exists()
    assert dst.suffix == ".png"


def test_oversized_png_converts_to_jpeg_when_opted_in(tmp_path, make_image):
    src = make_image(tmp_path / "big.png", width=800, height=600, noisy=True, quality=100)
    dst = tmp_path / "out" / "big.png"
    settings = _settings(
        tmp_path, max_size_mb=0.001, convert_to_jpeg_if_oversized=True, min_quality=10, quality_step=10
    )

    actual_dst = ImageCompressionService().process(src, dst, settings)

    assert actual_dst == dst.with_suffix(".jpg")
    assert actual_dst.exists()
    assert not dst.exists()  # the intermediate lossless attempt is removed
