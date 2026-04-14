import json
import importlib

from hsr_sim.models.schemas.character import CharacterConfig
from hsr_sim.models.schemas.light_cone import LightConeConfig
from hsr_sim.models.schemas.relics import RelicSetConfig

config_loader_module = importlib.import_module("hsr_sim.services.config_loader")


def _write_json(path, payload: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _character_payload(char_id: int, name: str) -> dict:
	return {
		"id": char_id,
		"name": name,
		"rarity": 5,
		"element": "quantum",
		"base_hp": 1000.0,
		"base_atk": 500.0,
		"base_def": 400.0,
		"base_spd": 120.0,
		"basic_atk": {
			"id": char_id + 1,
			"name": f"{name}_basic",
			"type": "basic",
			"description": "basic",
			"target_type": "single_target",
			"energy_gain": 20.0,
			"script": f"skills/{name}_basic",
		},
		"skill": {
			"id": char_id + 2,
			"name": f"{name}_skill",
			"type": "skill",
			"description": "skill",
			"target_type": "single_target",
			"energy_gain": 30.0,
			"script": f"skills/{name}_skill",
		},
		"ultimate": {
			"id": char_id + 3,
			"name": f"{name}_ultimate",
			"type": "ultimate",
			"description": "ultimate",
			"target_type": "aoe",
			"energy_gain": 5.0,
			"script": f"skills/{name}_ultimate",
		},
		"eidolons": [
			{
				"id": char_id + 4,
				"index": 1,
				"name": f"{name}_eidolon_1",
				"describe": "eidolon",
				"script": f"eidolons/{name}_eidolon_1",
			}
		],
		"talents": [
			{
				"id": char_id + 5,
				"name": f"{name}_talent",
				"description": "talent",
				"script": f"talent/{name}_talent",
			}
		],
		"technique": {
			"id": char_id + 6,
			"name": f"{name}_technique",
			"description": "technique",
			"script": f"technique/{name}_technique",
		},
		"bonus_abilities": [
			{
				"id": char_id + 7,
				"name": f"{name}_bonus_ability_1",
				"description": "bonus",
				"script": f"bonus_ability/{name}_bonus_ability_1",
			}
		],
		"stat_bonus": {"atk_percent": 0.1},
		"energy": {"energy_type": "standard", "max_energy": 120},
		"elation_skill": None,
		"memosprite": None,
	}


def _light_cone_payload(lc_id: int, name: str) -> dict:
	return {
		"id": lc_id,
		"name": name,
		"rarity": 5,
		"path": "hunt",
		"base_hp": 100.0,
		"base_atk": 60.0,
		"base_def": 40.0,
		"story": "story",
		"passive_skill": {
			"id": lc_id + 1,
			"name": f"{name}_passive",
			"description": "passive",
			"script": f"light_cones/{name}",
		},
	}


def _relic_piece_payload(piece_id: int, set_name: str, slot: str) -> dict:
	return {
		"id": piece_id,
		"name": f"{set_name}_{slot}",
		"relic_set": {
			"id": 20000000,
			"name": set_name,
			"passive_2_pc": {
				"id": 22000000,
				"name": f"{set_name}_2_pc",
				"description": "2pc",
				"script": f"{set_name}_2_pc",
			},
			"passive_4_pc": {
				"id": 23000000,
				"name": f"{set_name}_4_pc",
				"description": "4pc",
				"script": f"{set_name}_4_pc",
			},
		},
		"slot": slot,
		"story": "story",
	}


def test_config_loader_loads_all_sections(tmp_path, monkeypatch):
	configs_root = tmp_path / "configs"
	version = "v1.0"

	char_name = "test_char"
	char_dir = configs_root / version / "characters" / char_name
	_write_json(char_dir / f"{char_name}.json", _character_payload(10000000, char_name))
	(char_dir / "skills").mkdir(parents=True, exist_ok=True)
	(char_dir / "skills" / f"{char_name}_basic.py").write_text("", encoding="utf-8")
	(char_dir / "talent").mkdir(parents=True, exist_ok=True)
	(char_dir / "talent" / f"{char_name}_talent.py").write_text("", encoding="utf-8")
	(char_dir / "technique").mkdir(parents=True, exist_ok=True)
	(char_dir / "technique" / f"{char_name}_technique.py").write_text("", encoding="utf-8")
	(char_dir / "eidolons").mkdir(parents=True, exist_ok=True)
	(char_dir / "eidolons" / f"{char_name}_eidolon_1.py").write_text("", encoding="utf-8")
	(char_dir / "bonus_ability").mkdir(parents=True, exist_ok=True)
	(char_dir / "bonus_ability" / f"{char_name}_bonus_ability_1.py").write_text("", encoding="utf-8")

	lc_name = "test_lc"
	lc_dir = configs_root / version / "light_cones" / lc_name
	_write_json(lc_dir / f"{lc_name}.json", _light_cone_payload(30000000, lc_name))
	(lc_dir / f"{lc_name}.py").write_text("", encoding="utf-8")

	relic_set = "test_relic_set"
	relic_dir = configs_root / version / "relics" / relic_set
	_write_json(relic_dir / "head.json", _relic_piece_payload(21000000, relic_set, "head"))
	(relic_dir / f"{relic_set}_2_pc.py").write_text("", encoding="utf-8")
	(relic_dir / f"{relic_set}_4_pc.py").write_text("", encoding="utf-8")

	monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", configs_root)
	loader = config_loader_module.ConfigLoader()

	character = loader.get_character(char_name)
	assert character is not None
	assert isinstance(character["config"], CharacterConfig)
	assert character["config"].name == char_name
	assert character["scripts"]["skills"][f"{char_name}_basic"] == (
		f"configs.{version}.characters.{char_name}.skills.{char_name}_basic"
	)

	light_cone = loader.get_light_cone(lc_name)
	assert light_cone is not None
	assert isinstance(light_cone["config"], LightConeConfig)
	assert light_cone["script"] == f"configs.{version}.light_cones.{lc_name}.{lc_name}"

	relic = loader.get_relic_set(relic_set)
	assert relic is not None
	assert isinstance(relic["config"], RelicSetConfig)
	assert "head" in relic["pieces"]
	assert relic["scripts"][f"{relic_set}_2_pc"] == (
		f"configs.{version}.relics.{relic_set}.{relic_set}_2_pc"
	)


def test_config_loader_returns_latest_version_when_unspecified(tmp_path, monkeypatch):
	configs_root = tmp_path / "configs"
	char_name = "latest_char"

	char_v1 = configs_root / "v1.0" / "characters" / char_name
	_write_json(char_v1 / f"{char_name}.json", _character_payload(10000001, char_name))

	char_v2 = configs_root / "v2.0" / "characters" / char_name
	_write_json(char_v2 / f"{char_name}.json", _character_payload(20000001, char_name))

	monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", configs_root)
	loader = config_loader_module.ConfigLoader()

	latest = loader.get_character(char_name)
	explicit_v1 = loader.get_character(char_name, version="v1.0")

	assert latest is not None
	assert explicit_v1 is not None
	assert latest["config"].id == 20000001
	assert explicit_v1["config"].id == 10000001
	assert loader.get_character_versions(char_name) == ["v1.0", "v2.0"]
