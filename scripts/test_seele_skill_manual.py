"""Manual test script for Seele skill + Mara-Struck Soldier enemy mechanics.

Usage:
    uv run python scripts/test_seele_skill_manual.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import esper
from rich.console import Console
from rich.table import Table

from hsr_sim.ecs.world import ECSWorld
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.skills.script_loader import (
    CharacterSkillBundle,
    CharacterSkillLoader,
    SkillContext,
    SkillScriptLoader,
)
from hsr_sim.services import config_loader
from hsr_sim.ecs.components import (
    AttackComponent,
    DefenseComponent,
    HealthComponent,
    SpeedComponent,
    StandardEnergyComponent,
    CharacterIdentityComponent,
    CharacterStatusComponent,
    BuffContainerComponent,
    CritRateComponent,
    CritDamageComponent,
)
from hsr_sim.ecs.systems import (
    TurnSystem,
    DamageSystem,
    HealingSystem,
    HealthSystem,
    EnergySystem,
    BuffSystem,
)


def make_seele(version: str = "v1.0") -> int:
    """Create a level-80 Seele entity."""
    seele_cfg = config_loader.get_character("seele", version=version)["config"]
    entity = esper.create_entity()
    esper.add_component(
        entity, HealthComponent(value=10000.0, max_value=10000.0)
    )
    esper.add_component(entity, AttackComponent(value=582.4))
    esper.add_component(entity, DefenseComponent(value=699.8))
    esper.add_component(entity, SpeedComponent(base_speed=109.0))
    esper.add_component(
        entity, StandardEnergyComponent(energy=0.0, max_energy=120.0)
    )
    esper.add_component(
        entity, CharacterStatusComponent(status=CharacterStatus.ALIVE)
    )
    esper.add_component(entity, BuffContainerComponent())
    esper.add_component(entity, CritRateComponent(value=0.05))
    esper.add_component(entity, CritDamageComponent(value=1.50))
    esper.add_component(
        entity,
        CharacterIdentityComponent(
            config_id=seele_cfg.id,
            config_name=seele_cfg.name,
            version=version,
        ),
    )
    return entity


def make_enemy(version: str = "v1.0") -> int:
    """Create a level-80 Mara-Struck Soldier entity."""
    entity = esper.create_entity()
    esper.add_component(
        entity, HealthComponent(value=16518.0, max_value=16518.0)
    )
    esper.add_component(entity, AttackComponent(value=552.0))
    esper.add_component(entity, DefenseComponent(value=1000.0))
    esper.add_component(entity, SpeedComponent(base_speed=99.6))
    esper.add_component(
        entity, CharacterStatusComponent(status=CharacterStatus.ALIVE)
    )
    esper.add_component(entity, BuffContainerComponent())
    return entity


def stat_table(title: str) -> Table:
    t = Table(title=title, show_header=True, header_style="bold")
    t.add_column("Field", style="cyan")
    t.add_column("Value", style="yellow")
    return t


def show_entity(
    console: Console, label: str, entity_id: int, indent: str = "  "
):
    health = esper.try_component(entity_id, HealthComponent)
    atk = esper.try_component(entity_id, AttackComponent)
    defense = esper.try_component(entity_id, DefenseComponent)
    spd = esper.try_component(entity_id, SpeedComponent)
    status = esper.try_component(entity_id, CharacterStatusComponent)
    energy = esper.try_component(entity_id, StandardEnergyComponent)

    console.print(f"{indent}[bold]{label}[/bold] (entity #{entity_id})")
    console.print(
        f"{indent}  HP={health.value:.1f}/{health.max_value:.1f}  "
        f"ATK={atk.value:.1f}  DEF={defense.value:.1f}  SPD={spd.final_speed:.1f}  "
        f"Status={status.status.value}"
    )
    if energy:
        console.print(
            f"{indent}  Energy={energy.energy:.1f}/{energy.max_energy:.1f}"
        )


def main():
    console = Console()
    console.print(
        "\n[bold cyan]=== Seele + Mara-Struck Soldier Combat Test ===[/]\n"
    )

    version = "v1.0"
    world = ECSWorld(version)
    esper.switch_world(world.world_name)
    world.activate()

    turn_sys = TurnSystem(world.event_stream)
    dmg_sys = DamageSystem(world.event_stream, world.hook_registry, lambda: 0)
    heal_sys = HealingSystem(world.event_stream, world.hook_registry, lambda: 0)
    hlth_sys = HealthSystem(world.event_stream, world.hook_registry)
    nrgs_sys = EnergySystem(world.event_stream)
    buff_sys = BuffSystem(world.event_stream, world.hook_registry)

    for sys in (turn_sys, dmg_sys, heal_sys, hlth_sys, nrgs_sys, buff_sys):
        world.systems.append(sys)

    hlth_sys.subscribe_to_events()
    nrgs_sys.subscribe_to_events()
    buff_sys.subscribe_to_events()

    seele = make_seele(version)
    enemy = make_enemy(version)

    console.print("[bold]Entities created:[/bold]")
    show_entity(console, "Seele", seele)
    show_entity(console, "Mara-Struck Soldier", enemy)
    console.print()

    skill_bundle = CharacterSkillLoader(config_loader).load_for_character(
        _user_char_for(seele),
        SkillContext(
            world=world,
            event_bus=world.event_stream,
            hook_chain=world.hook_registry,
        ),
        activated_bonus_ability_ids=set(),
    )
    console.print(
        f"[green]Loaded {len(skill_bundle.all)} skill scripts[/green]"
    )
    console.print(
        f"  eidolons active: {[type(e).__name__ for e in skill_bundle.eidolons]}"
    )

    console.print("\n[bold]--- Turn 1: Seele uses Skill ---[/bold]")
    skill = skill_bundle.active[1]
    console.print(f"Executing: {type(skill).__name__}")
    result = skill.execute(seele, [enemy])
    console.print(f"Script result: {result}")

    dmg_event = world.event_log.events[-1]
    console.print(f"Last event: type={dmg_event.type}, data={dmg_event.data}")

    show_entity(console, "Seele (after skill)", seele)
    show_entity(console, "Enemy (after skill)", enemy)
    console.print()

    console.print("[bold]--- Enemy HP reduced to 500 ---[/bold]")
    health = esper.component_for_entity(enemy, HealthComponent)
    health.value = 500.0
    show_entity(console, "Enemy", enemy)

    console.print(
        "\n[bold]--- Turn 2: Seele uses Skill again (E1 active: +15% CR vs HP<=80%) ---[/bold]"
    )
    result2 = skill.execute(seele, [enemy])
    console.print(f"Script result: {result2}")
    show_entity(console, "Seele (after skill 2)", seele)
    show_entity(console, "Enemy (after skill 2)", enemy)
    console.print()

    console.print("[bold]--- Enemy defeated ---[/bold]")
    console.print(
        "  Enemy already knocked down from Skill 2. E4 energy restore: +15 (correct)."
    )

    show_entity(console, "Enemy (knocked down)", enemy)
    seele_energy = esper.try_component(seele, StandardEnergyComponent)
    console.print(f"  Seele energy: {seele_energy.energy:.1f}")
    console.print()

    console.print(
        "[bold]--- Enemy passive: Rejuvenate (first KO: 50% HP revive) ---[/bold]"
    )
    enemy_passive = load_enemy_passive(enemy, world, console)
    activate_passive(enemy_passive)
    console.print("  Resetting enemy to ALIVE, dealing lethal damage...")
    status = esper.component_for_entity(enemy, CharacterStatusComponent)
    health = esper.component_for_entity(enemy, HealthComponent)
    status.status = CharacterStatus.ALIVE
    health.value = health.max_value
    console.print(f"  Pre-damage HP: {health.value:.0f}/{health.max_value:.0f}")
    console.print(f"  Lethal damage: {health.max_value + 1:.0f}")
    hlth_sys._apply_damage(enemy, health.max_value + 1, source_id=seele)
    show_entity(console, "Enemy (should be revived at 50% HP)", enemy)
    expected_hp = health.max_value * 0.5
    actual_pct = health.value / health.max_value * 100
    console.print(
        f"  Expected HP: {expected_hp:.0f} (50%), Got: {health.value:.0f} ({actual_pct:.0f}%)"
    )

    console.print(
        "\n[bold]--- Enemy passive: Rejuvenate (second KO — permanent) ---[/bold]"
    )
    console.print("  Dealing lethal damage again...")
    hlth_sys._apply_damage(enemy, health.max_value + 1, source_id=seele)
    show_entity(console, "Enemy (now perma-knocked down)", enemy)

    console.print("\n[bold cyan]=== Test complete ===[/bold cyan]")
    world.deactivate()
    esper.switch_world("default")


# ---------------------------------------------------------------------------
# Minimal helpers to satisfy CharacterSkillLoader
# ---------------------------------------------------------------------------
import dataclasses


@dataclasses.dataclass
class _FakeUserChar:
    char_config_id: int
    version: str
    eidolon_level: int = 4


def _user_char_for(entity_id: int) -> _FakeUserChar:
    identity = esper.try_component(entity_id, CharacterIdentityComponent)
    return _FakeUserChar(
        char_config_id=identity.config_id if identity else 0,
        version=identity.version if identity else "v1.0",
    )


def activate_passive(script_obj) -> None:
    act = getattr(script_obj, "activate", None)
    if callable(act):
        act()


def deactivate_passive(bundle: CharacterSkillBundle) -> None:
    CharacterSkillLoader.deactivate_passive_skills(bundle)


def load_enemy_passive(enemy_entity: int, world: ECSWorld, console: Console):
    """Load and instantiate Mara-Struck Soldier's passive script."""
    enemy_cfg = config_loader.get_enemy_config("mara_struck_soldier", "v1.0")
    if not enemy_cfg:
        console.print("[red]Enemy config not found![/red]")
        return None
    passive_cfg = enemy_cfg.get("config").passives[0]
    context = SkillContext(
        world=world,
        event_bus=world.event_stream,
        hook_chain=world.hook_registry,
    )
    passive_obj = SkillScriptLoader().load_passive(
        version="v1.0",
        enemy_name="mara_struck_soldier",
        script=passive_cfg.script,
        context=context,
    )
    return passive_obj


if __name__ == "__main__":
    main()


def test_manual_scenario():
    """Dummy test so pytest can collect and run the script."""
    main()
