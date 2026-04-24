import copy
import importlib
import json


migrate_module = importlib.import_module("scripts.migrate_character_configs")


def _character_payload_without_energy() -> dict:
    return {
        "id": 10000000,
        "name": "seele",
        "rarity": 5,
        "element": "quantum",
        "base_hp": 1000.0,
        "base_atk": 777.0,
        "base_def": 500.0,
        "base_spd": 100.0,
        "basic_atk": {
            "id": 11000000,
            "name": "seele_basic",
            "type": "basic",
            "description": "TODO: fill description",
            "target_type": "single_target",
            "energy_gain": 0.0,
            "script": "skills/seele_basic_atk",
        },
        "skill": {
            "id": 12000000,
            "name": "seele_skill",
            "type": "skill",
            "description": "TODO: fill description",
            "target_type": "single_target",
            "energy_gain": 0.0,
            "script": "skills/seele_skill",
        },
        "ultimate": {
            "id": 13000000,
            "name": "seele_ultimate",
            "type": "ultimate",
            "description": "TODO: fill description",
            "target_type": "single_target",
            "energy_gain": 0.0,
            "script": "skills/seele_ultimate",
        },
        "eidolons": [],
        "talents": [],
        "technique": {
            "id": 16000000,
            "name": "seele_technique",
            "description": "TODO: fill technique description",
            "script": "technique/seele_technique",
        },
        "bonus_abilities": [],
        "stat_bonus": {"atk_percent": 0.0},
        "elation_skill": None,
        "memosprite": None,
    }


def test_deep_fill_missing_does_not_override_existing_values():
    target = {
        "energy": {
            "energy_type": "special_flux",
            "max_energy": 8,
        }
    }
    defaults = {
        "energy": {
            "energy_type": "standard",
            "max_energy": 120,
        }
    }

    merged = migrate_module._deep_fill_missing(copy.deepcopy(target), defaults)

    assert merged["energy"]["energy_type"] == "special_flux"
    assert merged["energy"]["max_energy"] == 8


def test_migrate_character_configs_fills_missing_energy_and_preserves_custom_data(
    tmp_path, monkeypatch
):
    configs_root = tmp_path / "configs"
    char_json = configs_root / "v1.0" / "characters" / "seele" / "seele.json"
    char_json.parent.mkdir(parents=True, exist_ok=True)
    payload = _character_payload_without_energy()
    char_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    monkeypatch.setattr(migrate_module, "CONFIGS_DIR", configs_root)
    stats = migrate_module.migrate_character_configs(version="v1.0", write=True)

    migrated = json.loads(char_json.read_text(encoding="utf-8"))

    assert stats["scanned"] == 1
    assert stats["updated"] == 1
    assert stats["errors"] == 0
    assert migrated["energy"] == {"energy_type": "standard", "max_energy": 120}
    assert migrated["base_atk"] == 777.0
