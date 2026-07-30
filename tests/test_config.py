from cimageoptimizer.infrastructure.config import load_settings, save_settings


def test_load_settings_returns_empty_dict_when_missing(tmp_path):
    assert load_settings(tmp_path / "settings.json") == {}


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "nested" / "settings.json"
    data = {"source_dir": "C:/src", "profile": "advanced"}

    save_settings(data, path)

    assert load_settings(path) == data


def test_load_settings_ignores_corrupt_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not valid json", encoding="utf-8")

    assert load_settings(path) == {}
