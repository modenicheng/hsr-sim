import json
import shutil

from hsr_sim.services import config_loader as config_loader_module


def test_config_loader_reads_real_repo_v1_data():
    loader = config_loader_module.ConfigLoader()

    seele_v1 = loader.get_character("seele", version="v1.0")
    assert seele_v1 is not None
    assert seele_v1["config"].name == "seele"
    assert seele_v1["config"].id == 10000000
    assert "skills" in seele_v1["scripts"]
    assert any(
        path.startswith("configs.v1.0.characters.seele.skills.")
        for path in seele_v1["scripts"]["skills"].values()
    )

    lc_v1 = loader.get_light_cone("in_the_night", version="v1.0")
    assert lc_v1 is not None
    assert lc_v1["config"].name == "in_the_night"
    assert lc_v1["script"] == "configs.v1.0.light_cones.in_the_night.in_the_night"

    relic_v1 = loader.get_relic_set("genius_of_brilliant_stars", version="v1.0")
    assert relic_v1 is not None
    assert relic_v1["config"].name == "genius_of_brilliant_stars"
    assert "head" in relic_v1["pieces"]


def test_config_loader_versioning_with_new_v2_seele(tmp_path, monkeypatch):
    source_configs = config_loader_module.CONFIGS_DIR
    temp_configs = tmp_path / "configs"

    shutil.copytree(source_configs / "v1.0", temp_configs / "v1.0")

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
    assert v1["config"].id == 10000000
    assert loader.get_character_versions("seele") == ["v1.0", "v2.0"]