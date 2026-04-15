from scripts import create_character
from scripts import create_buff
from scripts import create_enemy
from scripts import create_light_cone
from scripts import create_relic_set
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.skills.script_loader import DynamicClassLoader


def test_character_generator_outputs_loadable_scripts(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_character, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_character.run_create_character("alpha", "v1.0")

    loader = DynamicClassLoader()
    cls = loader.load_class(
        "configs.v1_0.characters.alpha.skills.alpha_basic_atk",
        expected_base_class=BaseSkill,
    )
    assert cls.__name__ == "AlphaBasicAtk"

    module = loader.load_module("configs.v1_0.characters.alpha.talent.alpha_talent")
    assert not hasattr(module, "apply")


def test_light_cone_generator_outputs_loadable_script(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_light_cone, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_light_cone.run_create_light_cone("beta_cone", "v1.0")

    loader = DynamicClassLoader()
    cls = loader.load_class(
        "configs.v1_0.light_cones.beta_cone.beta_cone",
        expected_base_class=BaseSkill,
    )
    assert cls.__name__ == "BetaCone"


def test_relic_generator_outputs_loadable_scripts(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_relic_set, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_relic_set.run_create_relic_set("gamma_set", "v1.0", "relics")

    loader = DynamicClassLoader()
    cls_2pc = loader.load_class(
        "configs.v1_0.relics.gamma_set.gamma_set_2_pc",
        expected_base_class=BaseSkill,
    )
    cls_4pc = loader.load_class(
        "configs.v1_0.relics.gamma_set.gamma_set_4_pc",
        expected_base_class=BaseSkill,
    )

    assert cls_2pc.__name__ == "GammaSet2Pc"
    assert cls_4pc.__name__ == "GammaSet4Pc"


def test_buff_generator_outputs_loadable_global_script(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_buff, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_buff.run_create_buff("delta_buff", "v1.0")

    loader = DynamicClassLoader()
    cls = loader.load_class(
        "configs.v1_0.buffs.delta_buff.delta_buff",
        expected_base_class=BaseSkill,
    )

    assert cls.__name__ == "DeltaBuff"


def test_buff_generator_outputs_loadable_character_script(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_buff, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_buff.run_create_buff(
        "epsilon_buff",
        "v1.0",
        character_name="alpha",
        character_id=10000001,
    )

    loader = DynamicClassLoader()
    cls = loader.load_class(
        "configs.v1_0.characters.alpha.buffs.epsilon_buff.epsilon_buff",
        expected_base_class=BaseSkill,
    )

    assert cls.__name__ == "EpsilonBuff"


def test_enemy_generator_outputs_loadable_scripts(tmp_path, monkeypatch):
    configs_root = tmp_path / "configs"
    monkeypatch.setattr(create_enemy, "CONFIGS_DIR", configs_root)
    monkeypatch.setattr("hsr_sim.skills.script_loader.PROJECT_ROOT", tmp_path)

    create_enemy.run_create_enemy("zeta_enemy", "v1.0")

    loader = DynamicClassLoader()
    skill_cls = loader.load_class(
        "configs.v1_0.enemies.zeta_enemy.skills.zeta_enemy_skill",
        expected_base_class=BaseSkill,
    )
    passive_cls = loader.load_class(
        "configs.v1_0.enemies.zeta_enemy.passives.zeta_enemy_passive",
        expected_base_class=BaseSkill,
    )

    assert skill_cls.__name__ == "ZetaEnemySkill"
    assert passive_cls.__name__ == "ZetaEnemyPassive"
