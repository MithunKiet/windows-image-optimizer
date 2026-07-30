from cimageoptimizer.application.services.discovery_service import FileDiscoveryService


def test_finds_files_missing_from_output(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    make_image(source / "sub" / "b.jpg")
    (source / "notes.txt").write_text("hi")

    missing = FileDiscoveryService().find_missing_files(source, output, images_only=False)

    assert {p.name for p in missing} == {"a.jpg", "b.jpg", "notes.txt"}


def test_images_only_skips_non_images(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    (source / "notes.txt").write_text("hi")

    missing = FileDiscoveryService().find_missing_files(source, output, images_only=True)

    assert [p.name for p in missing] == ["a.jpg"]


def test_skips_files_already_present_in_output(tmp_path, make_image):
    source = tmp_path / "source"
    output = tmp_path / "output"
    make_image(source / "a.jpg")
    make_image(output / "a.jpg")

    missing = FileDiscoveryService().find_missing_files(source, output, images_only=False)

    assert missing == []
