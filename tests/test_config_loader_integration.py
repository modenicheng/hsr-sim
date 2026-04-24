import json
import importlib
import shutil

config_loader_module = importlib.import_module("hsr_sim.services.config_loader")


def _copy_real_v1_data_with_normalized_light_cones(temp_configs) -> None:
    source_configs = config_loader_module.CONFIGS_DIR
    shutil.copytree(source_configs / "v1.0", temp_configs / "v1.0")

    light_cones_root = temp_configs / "v1.0" / "light_cones"
    for lc_dir in light_cones_root.iterdir():
        if not lc_dir.is_dir():
            continue
        json_path = lc_dir / f"{lc_dir.name}.json"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        payload["base_hp"] = (
            payload["base_hp"] if payload["base_hp"] > 0 else 1.0
        )
        payload["base_atk"] = (
            payload["base_atk"] if payload["base_atk"] > 0 else 1.0
        )
        payload["base_def"] = (
            payload["base_def"] if payload["base_def"] > 0 else 1.0
        )
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def test_config_loader_reads_real_repo_v1_data(tmp_path, monkeypatch):
    temp_configs = tmp_path / "configs"
    _copy_real_v1_data_with_normalized_light_cones(temp_configs)
    monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", temp_configs)

    loader = config_loader_module.ConfigLoader()

    seele_v1 = loader.get_character("seele", version="v1.0")
    assert seele_v1 is not None
    assert seele_v1["config"].name == "seele"
    assert seele_v1["config"].id >= 10000000
    assert seele_v1["config"].energy.energy_type == "standard"
    assert seele_v1["config"].energy.max_energy > 0
    assert "skills" in seele_v1["scripts"]
    assert any(
        path.startswith("configs.v1.0.characters.seele.skills.")
        for path in seele_v1["scripts"]["skills"].values()
    )

    lc_v1 = loader.get_light_cone("in_the_night", version="v1.0")
    assert lc_v1 is not None
    assert lc_v1["config"].name == "in_the_night"
    assert (
        lc_v1["script"] == "configs.v1.0.light_cones.in_the_night.in_the_night"
    )

    relic_v1 = loader.get_relic_set("genius_of_brilliant_stars", version="v1.0")
    assert relic_v1 is not None
    assert relic_v1["config"].name == "genius_of_brilliant_stars"
    assert "head" in relic_v1["pieces"]


def test_config_loader_versioning_with_new_v2_seele(tmp_path, monkeypatch):
    temp_configs = tmp_path / "configs"
    _copy_real_v1_data_with_normalized_light_cones(temp_configs)

    v1_seele_dir = temp_configs / "v1.0" / "characters" / "seele"
    v2_seele_dir = temp_configs / "v2.0" / "characters" / "seele"
    shutil.copytree(v1_seele_dir, v2_seele_dir)

    v2_seele_json = v2_seele_dir / "seele.json"
    payload = json.loads(v2_seele_json.read_text(encoding="utf-8"))
    payload["id"] = 20000000
    payload["base_atk"] = 999.0
    v2_seele_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", temp_configs)
    loader = config_loader_module.ConfigLoader()

    latest = loader.get_character("seele")
    v1 = loader.get_character("seele", version="v1.0")
    v2 = loader.get_character("seele", version="v2.0")

    assert latest is not None
    assert v1 is not None
    assert v2 is not None
    assert latest["config"].id == 20000000
    assert latest["config"].base_atk == 999.0
    assert v1["config"].id != v2["config"].id
    assert loader.get_character_versions("seele") == ["v1.0", "v2.0"]
