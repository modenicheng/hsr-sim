import pytest

from hsr_sim.utils.import_utils import import_class


def test_import_class_loads_expected_class(tmp_path, monkeypatch):
    module_file = tmp_path / "fake_module.py"
    module_file.write_text(
        "class TargetClass:\n"
        "    value = 42\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    loaded = import_class("fake_module.target_class")

    assert loaded.__name__ == "TargetClass"
    assert loaded.value == 42


def test_import_class_raises_when_class_not_found(tmp_path, monkeypatch):
    module_file = tmp_path / "other_module.py"
    module_file.write_text("class ExistingClass:\n    pass\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(AttributeError):
        import_class("other_module.missing_class")