"""BattleSession 集成测试。"""

import esper
import pytest
from hsr_sim.services import config_loader

from hsr_sim.battle.session import BattleSession
from hsr_sim.ecs.components import (
    AttackComponent,
    BuffContainerComponent,
    CharacterIdentityComponent,
    CharacterStatusComponent,
    DefenseComponent,
    HealthComponent,
    SpeedComponent,
)
from hsr_sim.models.battle_state import BattleState, ActionInput
from hsr_sim.models.character_status import CharacterStatus


@pytest.fixture
def battle_session():
    """创建测试用战斗会话。"""
    session = BattleSession(config_version="v1.0")
    yield session
    # 清理
    if session.world:
        session.cleanup()


def test_battle_session_initialization(battle_session):
    """测试 BattleSession 初始化。"""
    assert battle_session.state == BattleState.IDLE
    assert battle_session.current_tick == 0
    assert battle_session.current_turn == 0
    assert battle_session.world is not None
    assert battle_session.turn_system is not None
    assert battle_session.damage_system is not None


def test_battle_session_has_all_systems(battle_session):
    """测试所有系统已注册。"""
    system_types = [type(sys).__name__ for sys in battle_session.world.systems]
    assert "TurnSystem" in system_types
    assert "DamageSystem" in system_types
    assert "HealingSystem" in system_types
    assert "HealthSystem" in system_types
    assert "EnergySystem" in system_types
    assert "BuffSystem" in system_types


def test_battle_session_cleanup(battle_session):
    """测试资源清理。"""
    battle_session.cleanup()
    # 应该不抛出异常
    assert True


def test_action_input_validation():
    """测试行动输入结构。"""
    action = ActionInput(actor_id=1, action_type="BASIC_ATK", targets=[2])
    assert action.actor_id == 1
    assert action.action_type == "BASIC_ATK"
    assert action.targets == [2]


def _create_combat_entity(battle_session, hp=1000, atk=100, defense=100, speed=100, identity=None):
    """Create entity inside BattleSession's world (v1.0)."""
    esper.switch_world(battle_session.world.world_name)
    entity = esper.create_entity()
    esper.add_component(entity, HealthComponent(value=hp, max_value=hp))
    esper.add_component(entity, AttackComponent(value=atk))
    esper.add_component(entity, DefenseComponent(value=defense))
    esper.add_component(entity, SpeedComponent(base_speed=speed))
    esper.add_component(
        entity,
        CharacterStatusComponent(status=CharacterStatus.ALIVE),
    )
    esper.add_component(entity, BuffContainerComponent())
    if identity is not None:
        esper.add_component(entity, identity)
    return entity


def _health_value(entity_id: int) -> float:
    health = esper.try_component(entity_id, HealthComponent)
    assert health is not None
    return health.value


def test_submit_action_applies_damage_and_advances_turn(battle_session):
    attacker = _create_combat_entity(battle_session, hp=1200, atk=120, defense=80, speed=120)
    defender = _create_combat_entity(battle_session, hp=900, atk=90, defense=90, speed=90)

    battle_session.start(team_ids=[attacker], enemy_ids=[defender])
    assert battle_session.state == BattleState.WAITING_ACTION
    assert battle_session.get_current_actor() == attacker

    hp_before = _health_value(defender)
    ok = battle_session.submit_action(
        ActionInput(
            actor_id=attacker,
            action_type="basic",
            targets=[defender],
            params={"base_damage": 100.0},
        )
    )

    hp_after = _health_value(defender)
    assert ok is True
    assert hp_after < hp_before


def test_submit_action_unknown_type_returns_false_without_effect(
    battle_session,
):
    attacker = _create_combat_entity(battle_session, hp=1200, atk=120, defense=80, speed=120)
    defender = _create_combat_entity(battle_session, hp=900, atk=90, defense=90, speed=90)

    battle_session.start(team_ids=[attacker], enemy_ids=[defender])
    hp_before = _health_value(defender)

    ok = battle_session.submit_action(
        ActionInput(
            actor_id=attacker,
            action_type="unknown_action",
            targets=[defender],
        )
    )

    hp_after = _health_value(defender)
    assert ok is False
    assert hp_after == hp_before
    assert battle_session.state == BattleState.WAITING_ACTION


def test_submit_action_loads_skill_script_by_skill_id(
    monkeypatch, battle_session
):
    payload = config_loader.get_character("seele", version="v1.0")
    assert payload is not None
    char_config = payload["config"]

    attacker = _create_combat_entity(
        battle_session,
        hp=1200,
        atk=120,
        defense=80,
        speed=120,
        identity=CharacterIdentityComponent(
            config_id=char_config.id,
            config_name=char_config.name,
            version="v1.0",
        ),
    )
    defender = _create_combat_entity(battle_session, hp=900, atk=90, defense=90, speed=90)

    class _FakeSkill:
        def __init__(self):
            self.called = False

        def execute(self, caster, targets):
            self.called = True
            assert caster == attacker
            assert targets == [defender]
            return {
                "effect": "damage",
                "base_damage": 123.0,
                "skill_name": "fake scripted skill",
            }

    fake_skill = _FakeSkill()

    monkeypatch.setattr(
        battle_session._skill_loader,
        "load_skill",
        lambda **kwargs: fake_skill,
    )

    battle_session.start(team_ids=[attacker], enemy_ids=[defender])
    hp_before = _health_value(defender)

    ok = battle_session.submit_action(
        ActionInput(
            actor_id=attacker,
            action_type="skill",
            targets=[defender],
            params={"skill_id": char_config.skill.id},
        )
    )

    hp_after = _health_value(defender)
    assert ok is True
    assert fake_skill.called is True
    assert hp_after < hp_before
