import importlib
import json

from hsr_sim.models.schemas.buff import BuffConfig

config_loader_module = importlib.import_module("hsr_sim.services.config_loader")


def _write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _character_payload() -> dict:
    return {
        "id": 10010001,
        "name": "cache_char",
        "rarity": 5,
        "element": "quantum",
        "base_hp": 1000.0,
        "base_atk": 500.0,
        "base_def": 400.0,
        "base_spd": 120.0,
        "basic_atk": {
            "id": 10010002,
            "name": "cache_basic",
            "type": "basic",
            "description": "basic",
            "target_type": "single_target",
            "energy_gain": 20.0,
            "script": "skills/cache_basic",
        },
        "skill": {
            "id": 10010003,
            "name": "cache_skill",
            "type": "skill",
            "description": "skill",
            "target_type": "single_target",
            "energy_gain": 30.0,
            "script": "skills/cache_skill",
        },
        "ultimate": {
            "id": 10010004,
            "name": "cache_ultimate",
            "type": "ultimate",
            "description": "ultimate",
            "target_type": "aoe",
            "energy_gain": 5.0,
            "script": "skills/cache_ultimate",
        },
        "eidolons": [],
        "talents": [],
        "technique": {
            "id": 10010005,
            "name": "cache_technique",
            "description": "technique",
            "script": "technique/cache_technique",
        },
        "bonus_abilities": [],
        "stat_bonus": {"atk_percent": 0.1},
        "energy": {"energy_type": "standard", "max_energy": 120},
        "elation_skill": None,
        "memosprite": None,
    }


def _light_cone_payload() -> dict:
    return {
        "id": 30010001,
        "name": "cache_lc",
        "rarity": 5,
        "path": "hunt",
        "base_hp": 100.0,
        "base_atk": 60.0,
        "base_def": 40.0,
        "story": "story",
        "passive_skill": {
            "id": 30010002,
            "name": "cache_passive",
            "description": "passive",
            "script": "light_cones/cache_lc",
        },
    }


def _relic_payload() -> dict:
    return {
        "id": 21010001,
        "name": "cache_set_head",
        "relic_set": {
            "id": 21010000,
            "name": "cache_set",
            "passive_2_pc": {
                "id": 21010010,
                "name": "cache_set_2_pc",
                "description": "2pc",
                "script": "cache_set_2_pc",
            },
            "passive_4_pc": None,
        },
        "slot": "head",
        "story": "story",
    }


def test_config_loader_supports_id_cache_and_buffs(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    version = "v1.0"

    _write_json(
        configs_root
        / version
        / "characters"
        / "cache_char"
        / "cache_char.json",
        _character_payload(),
    )
    _write_json(
        configs_root / version / "light_cones" / "cache_lc" / "cache_lc.json",
        _light_cone_payload(),
    )
    _write_json(
        configs_root / version / "relics" / "cache_set" / "head.json",
        _relic_payload(),
    )
    _write_json(
        configs_root / version / "buffs" / "team_buff" / "team_buff.json",
        {
            "id": 91001,
            "name": "team_buff",
            "description": "team buff",
            "scope": "global",
            "max_stacks": 1,
            "default_duration": 2,
            "dispelable": False,
            "script": "buffs/team_buff/team_buff",
            "params": {"atk_percent": 0.12},
        },
    )
    (
        configs_root / version / "buffs" / "team_buff" / "team_buff.py"
    ).write_text("", encoding="utf-8")

    monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", configs_root)
    loader = config_loader_module.ConfigLoader()

    assert loader.get_character_by_id(10010001) is not None
    assert loader.get_light_cone_by_id(30010001) is not None
    relic_data = loader.get_relic_set_by_id(21010000)
    assert relic_data is not None
    assert relic_data["config"].name == "cache_set"

    buff = loader.get_buff("team_buff")
    assert buff is not None
    assert isinstance(buff["config"], BuffConfig)
    assert buff["config"].params["atk_percent"] == 0.12
    assert buff["config"].default_duration == 2
    assert buff["config"].name == "team_buff"

    buff_by_id = loader.get_buff_by_id(91001)
    assert buff_by_id is not None
    assert loader.get_buff_versions("team_buff") == ["v1.0"]
    assert len(loader.get_all_buffs()) == 1


def test_config_loader_prefers_character_specific_buff_over_global_buff(
    tmp_path,
    monkeypatch,
):
    configs_root = tmp_path / "configs"
    version = "v1.0"
    char_name = "cache_char"

    _write_json(
        configs_root / version / "characters" / char_name / f"{char_name}.json",
        _character_payload(),
    )

    _write_json(
        configs_root / version / "buffs" / "common" / "spd_boost.json",
        {
            "id": 91001,
            "name": "spd_boost",
            "description": "global speed buff",
            "scope": "global",
            "max_stacks": 1,
            "default_duration": 1,
            "dispelable": True,
            "script": "buffs/common/spd_boost",
            "params": {"spd_percent": 0.12},
        },
    )
    (configs_root / version / "buffs" / "common" / "spd_boost.py").write_text(
        "", encoding="utf-8"
    )

    _write_json(
        configs_root
        / version
        / "characters"
        / char_name
        / "buffs"
        / "spd_boost"
        / "spd_boost.json",
        {
            "id": 91001,
            "name": "spd_boost",
            "description": "character speed buff",
            "scope": "character",
            "max_stacks": 2,
            "default_duration": 3,
            "dispelable": True,
            "script": "characters/cache_char/buffs/spd_boost/spd_boost",
            "params": {"spd_percent": 0.25},
            "character_id": 10010001,
        },
    )
    (
        configs_root
        / version
        / "characters"
        / char_name
        / "buffs"
        / "spd_boost"
        / "spd_boost.py"
    ).write_text("", encoding="utf-8")

    monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", configs_root)
    loader = config_loader_module.ConfigLoader()

    global_buff = loader.get_buff("spd_boost")
    override_buff = loader.get_buff("spd_boost", character_id=10010001)
    override_buff_by_id = loader.get_buff_by_id(91001, character_id=10010001)

    assert global_buff is not None
    assert override_buff is not None
    assert override_buff_by_id is not None
    assert isinstance(global_buff["config"], BuffConfig)
    assert isinstance(override_buff["config"], BuffConfig)
    assert isinstance(override_buff_by_id["config"], BuffConfig)
    assert global_buff["config"].name == "spd_boost"
    assert override_buff["config"].name == "spd_boost"
    assert override_buff_by_id["config"].name == "spd_boost"
    assert loader.get_buff_versions("spd_boost", character_id=10010001) == [
        "v1.0"
    ]
    assert len(loader.get_all_buffs()) == 1
    assert len(loader.get_all_buffs(character_id=10010001)) == 1
