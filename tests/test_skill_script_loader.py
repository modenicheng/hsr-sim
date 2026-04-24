import importlib
from pathlib import Path

import pytest

from scripts import create_character
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.skills.script_loader import CharacterSkillLoader
from hsr_sim.skills.script_loader import DynamicClassLoader
from hsr_sim.skills.script_loader import SkillClassNotFoundError
from hsr_sim.skills.script_loader import SkillContext
from hsr_sim.skills.script_loader import SkillScriptLoader


def test_skill_script_loader_rejects_function_style_scripts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    skill_file = (
        tmp_path
        / "configs"
        / "v1.0"
        / "characters"
        / "legacy_char"
        / "skills"
        / "legacy_skill.py"
    )
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        "\n".join(
            [
                "def apply(context):",
                "    _ = context",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    loader = SkillScriptLoader()
    context = SkillContext()

    with pytest.raises(SkillClassNotFoundError):
        loader.load_skill(
            version="v1.0",
            char_name="legacy_char",
            script="skills/legacy_skill",
            context=context,
            skill_type="skill",
        )


def test_dynamic_class_loader_imports_class_script_from_file_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    skill_file = (
        tmp_path
        / "configs"
        / "v1.0"
        / "characters"
        / "temp_char"
        / "skills"
        / "temp_char_skill.py"
    )
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        "\n".join(
            [
                "from hsr_sim.skills.script_loader import BaseSkill",
                "",
                "class TempCharSkill(BaseSkill):",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    loader = DynamicClassLoader()
    cls = loader.load_class(
        "configs.v1_0.characters.temp_char.skills.temp_char_skill",
        expected_base_class=BaseSkill,
    )

    assert cls.__name__ == "TempCharSkill"


def test_character_skill_loader_aggregates_by_type(
    tmp_path: Path, monkeypatch
) -> None:
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_character, "CONFIGS_DIR", configs_root)
    create_character.run_create_character("alpha", "v1.0")

    config_loader_module = importlib.import_module(
        "hsr_sim.services.config_loader"
    )
    monkeypatch.setattr(config_loader_module, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    config_loader = config_loader_module.ConfigLoader()
    script_loader = SkillScriptLoader()
    loader = CharacterSkillLoader(
        config_loader=config_loader, script_loader=script_loader
    )

    character_payload = config_loader.get_character("alpha", version="v1.0")
    assert character_payload is not None
    character_config = character_payload["config"]

    character = UserCharacter(
        char_config_id=character_config.id,
        version="v1.0",
        level=80,
        eidolon_level=2,
    )
    context = SkillContext(config_loader=config_loader)

    bundle = loader.load_for_character(
        character,
        context,
        activated_bonus_ability_ids={
            character_config.bonus_abilities[0].id,
            character_config.bonus_abilities[2].id,
        },
    )

    assert len(bundle.active) == 3
    assert len(bundle.talents) == 1
    assert len(bundle.eidolons) == 2
    assert len(bundle.bonus_abilities) == 2
    assert len(bundle.technique) == 1
    assert len(bundle.all) == 9
