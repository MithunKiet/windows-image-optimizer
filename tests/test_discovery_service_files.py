from cimageoptimizer.application.services.discovery_service import FileDiscoveryService


def test_finds_missing_files_from_explicit_list(tmp_path, make_image):
    output = tmp_path / "output"
    a = make_image(tmp_path / "somewhere" / "a.jpg")
    b = make_image(tmp_path / "elsewhere" / "b.jpg")

    missing = FileDiscoveryService().find_missing_from_files([a, b], output, images_only=False)

    assert set(missing) == {a, b}


def test_images_only_filters_explicit_list(tmp_path, make_image):
    output = tmp_path / "output"
    image = make_image(tmp_path / "a.jpg")
    other = tmp_path / "notes.txt"
    other.write_text("hi")

    missing = FileDiscoveryService().find_missing_from_files([image, other], output, images_only=True)

    assert missing == [image]


def test_skips_files_already_present_by_name_in_output(tmp_path, make_image):
    output = tmp_path / "output"
    src = make_image(tmp_path / "src" / "a.jpg")
    make_image(output / "a.jpg")

    missing = FileDiscoveryService().find_missing_from_files([src], output, images_only=False)

    assert missing == []


def test_overwrite_existing_includes_files_already_present_in_output(tmp_path, make_image):
    output = tmp_path / "output"
    src = make_image(tmp_path / "src" / "a.jpg")
    make_image(output / "a.jpg")

    missing = FileDiscoveryService().find_missing_from_files(
        [src], output, images_only=False, overwrite_existing=True
    )

    assert missing == [src]
