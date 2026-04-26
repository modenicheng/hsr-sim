"""Seele Battle Simulation -- turn-based combat simulation.

Demonstrates Seele's skill, ultimate, talent (resurgence), and eidolon effects.

Run:
    uv run python scripts/test_seele_battle.py
"""

from __future__ import annotations

import dataclasses
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import esper
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from hsr_sim.ecs.world import ECSWorld
from hsr_sim.ecs.systems import (
    TurnSystem,
    DamageSystem,
    HealingSystem,
    HealthSystem,
    EnergySystem,
    BuffSystem,
)
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
    StackComponent,
    SkillPointComponent,
)
from hsr_sim.events.types import EventType
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.skills.script_loader import (
    CharacterSkillLoader,
    SkillContext,
    SkillScriptLoader,
)
from hsr_sim.services import config_loader

SEELE_CONFIG_ID = 10000000
SPD_BUFF_AMOUNT = 25.0
STACK_TYPE = "seele_spd_boost"
SKILL_SP_COST = 1
BASIC_SP_GAIN = 1
MAX_SP = 5
BASIC_DMG_MULTIPLIER = 1.0


def make_seele(version: str = "v1.0") -> int:
    seele_cfg = config_loader.get_character("seele", version)["config"]
    e = esper.create_entity()
    esper.add_component(e, HealthComponent(value=10000.0, max_value=10000.0))
    esper.add_component(e, AttackComponent(value=1582.4))
    esper.add_component(e, DefenseComponent(value=1699.8))
    esper.add_component(e, SpeedComponent(base_speed=149.0))
    esper.add_component(
        e, StandardEnergyComponent(energy=30.0, max_energy=120.0)
    )
    esper.add_component(
        e, SkillPointComponent(current=MAX_SP, max_value=MAX_SP)
    )
    esper.add_component(
        e, CharacterStatusComponent(status=CharacterStatus.ALIVE)
    )
    esper.add_component(e, BuffContainerComponent())
    esper.add_component(e, CritRateComponent(value=0.65))
    esper.add_component(e, CritDamageComponent(value=2.50))
    esper.add_component(
        e,
        CharacterIdentityComponent(
            config_id=seele_cfg.id,
            config_name=seele_cfg.name,
            version=version,
        ),
    )
    return e


def make_enemy(version: str = "v1.0") -> int:
    cfg = config_loader.get_enemy_config("mara_struck_soldier", version)[
        "config"
    ]
    e = esper.create_entity()
    esper.add_component(
        e, HealthComponent(value=cfg.base_hp, max_value=cfg.base_hp)
    )
    esper.add_component(e, AttackComponent(value=cfg.base_atk))
    esper.add_component(e, DefenseComponent(value=cfg.base_def))
    esper.add_component(e, SpeedComponent(base_speed=cfg.base_spd))
    esper.add_component(
        e, CharacterStatusComponent(status=CharacterStatus.ALIVE)
    )
    esper.add_component(e, BuffContainerComponent())
    return e


@dataclasses.dataclass
class _FakeUserChar:
    char_config_id: int
    version: str
    eidolon_level: int = 0


def make_status_table(entities: list[tuple[str, int]]) -> Table:
    t = Table(show_header=True, header_style="bold", box=box.ROUNDED)
    t.add_column("Entity", style="cyan")
    t.add_column("HP", style="green")
    t.add_column("SPD", style="yellow")
    t.add_column("Energy", style="magenta")
    t.add_column("Status", style="bold")
    for label, eid in entities:
        hp = esper.try_component(eid, HealthComponent)
        spd = esper.try_component(eid, SpeedComponent)
        energy = esper.try_component(eid, StandardEnergyComponent)
        status = esper.try_component(eid, CharacterStatusComponent)
        hp_str = f"{hp.value:.0f}/{hp.max_value:.0f}" if hp else "?"
        spd_str = f"{spd.final_speed:.1f}" if spd else "?"
        en_str = (
            f"{energy.energy:.0f}/{energy.max_energy:.0f}" if energy else "?"
        )
        st_str = status.status.value if status else "?"
        t.add_row(label, hp_str, spd_str, en_str, st_str)
    return t


def alive(entity_id: int) -> bool:
    s = esper.try_component(entity_id, CharacterStatusComponent)
    return s is not None and s.status == CharacterStatus.ALIVE


def render_action_bar(
    entities: list[tuple[str, int]],
    current_actor: int,
    turn_sys: TurnSystem,
) -> str:
    entries = turn_sys.action_queue.sorted_entries()
    parts = []
    for eid, av in entries:
        label = next((lbl for lbl, e in entities if e == eid), f"#{eid}")
        spd = esper.try_component(eid, SpeedComponent)
        marker = ">>>" if eid == current_actor else "   "
        spd_str = f"{spd.final_speed:.0f}" if spd else "?"
        parts.append(f"{marker}{label}[SPD={spd_str}, AV={av:.1f}]")
    return "[bold]Action Bar:[/bold]  " + "  ".join(parts)


def render_skill_point_bar(entity_id: int) -> str:
    sp = esper.try_component(entity_id, SkillPointComponent)
    if not sp:
        return "[bold]SP:[/bold] ?/?"
    filled = "#" * sp.current
    empty = "-" * (sp.max_value - sp.current)
    return f"[bold]SP:[/bold] {filled}{empty} {sp.current}/{sp.max_value}"


def _get_spd_stack(entity: int) -> StackComponent:
    stack = esper.try_component(entity, StackComponent)
    if stack is None:
        stack = StackComponent(stack_type=STACK_TYPE, current=0, max=1)
        esper.add_component(entity, stack)
    return stack


def consume_skill_point(entity_id: int) -> bool:
    sp = esper.component_for_entity(entity_id, SkillPointComponent)
    if sp.current < SKILL_SP_COST:
        return False
    sp.current -= SKILL_SP_COST
    return True


def restore_skill_point(entity_id: int) -> None:
    sp = esper.component_for_entity(entity_id, SkillPointComponent)
    sp.current = min(sp.current + BASIC_SP_GAIN, sp.max_value)


def execute_seele_action(
    seele: int,
    target: int,
    target_label: str,
    seele_skill_script,
    dmg_sys,
    resurgence_active: bool = False,
    console: Console | None = None,
):
    """Execute Seele's action (skill or basic), return (hp_before, hp_after)."""
    tgt_hp = esper.component_for_entity(target, HealthComponent)
    hp_pct = tgt_hp.value / tgt_hp.max_value * 100

    sp = esper.component_for_entity(seele, SkillPointComponent)
    has_sp = consume_skill_point(seele)

    suffix = " [bold magenta][Resurgence][/]" if resurgence_active else ""

    if has_sp:
        sp_before = sp.current + SKILL_SP_COST
        if console:
            console.print(
                "\n[bold yellow]> Seele[/] -- [bold]Skill[/] -> "
                + target_label
                + f" [dim](SP {sp_before}->{sp.current})[/dim]"
                + suffix
            )
            if hp_pct <= 80:
                console.print(
                    "  [dim]E1 active: target HP "
                    + f"{hp_pct:.0f}% <= 80% (+15% CR)[/dim]"
                )

        spd_before = esper.component_for_entity(seele, SpeedComponent)
        spd_before_val = spd_before.final_speed
        hp_before = tgt_hp.value

        seele_skill_script.execute(seele, [target])

        hp_after = esper.component_for_entity(target, HealthComponent).value
        dmg_dealt = hp_before - hp_after
        if console:
            console.print("  [red]Quantum DMG: " + f"{dmg_dealt:.0f}" + "[/]")
            console.print(
                "  "
                + target_label
                + " HP: "
                + f"{hp_before:.0f} -> {max(hp_after, 0):.0f}"
            )

        spd_after = esper.component_for_entity(seele, SpeedComponent)
        spd_after_val = spd_after.final_speed
        stack_after = _get_spd_stack(seele)
        stack_info = (
            "(" + str(stack_after.current) + "/" + str(stack_after.max) + ")"
        )
        if console:
            console.print(
                "  [cyan]SPD: "
                + f"{spd_before_val:.1f} -> {spd_after_val:.1f}"
                + " (+"
                + f"{SPD_BUFF_AMOUNT * stack_after.current:.1f}) "
                + stack_info
                + "[/]"
            )

        return hp_before, hp_after
    else:
        restore_skill_point(seele)
        seele_atk = esper.component_for_entity(seele, AttackComponent).value
        if console:
            console.print(
                "\n[bold yellow]> Seele[/] -- [bold dim]Basic Attack[/] -> "
                + target_label
                + f" [dim](SP {sp.current - 1}->{sp.current})[/dim]"
                + suffix
            )
        hp_before = tgt_hp.value
        dmg_sys.calculate_and_apply_damage(
            attacker_id=seele,
            defender_id=target,
            base_damage=seele_atk * BASIC_DMG_MULTIPLIER,
            damage_type="quantum",
        )
        hp_after = esper.component_for_entity(target, HealthComponent).value
        dmg_dealt = hp_before - hp_after
        if console:
            console.print("  [red]Quantum DMG: " + f"{dmg_dealt:.0f}" + "[/]")
            console.print(
                "  "
                + target_label
                + " HP: "
                + f"{hp_before:.0f} -> {max(hp_after, 0):.0f}"
            )
        return hp_before, hp_after


def main():
    version = "v1.0"
    random.seed(42)

    console = Console()
    console.print(
        Panel(
            "[bold cyan]Seele Battle Simulation[/]\n"
            "[dim]E4 enabled  |  2x Mara-Struck Soldiers  |  "
            "Ult + Resurgence  |  SP x/5[/]",
            box=box.DOUBLE,
        )
    )

    world = ECSWorld(version)
    esper.switch_world(world.world_name)
    world.activate()

    turn_sys = TurnSystem(world.event_stream)
    dmg_sys = DamageSystem(world.event_stream, world.hook_registry, lambda: 0)
    heal_sys = HealingSystem(world.event_stream, world.hook_registry, lambda: 0)
    hlth_sys = HealthSystem(world.event_stream, world.hook_registry)
    nrg_sys = EnergySystem(world.event_stream)
    buff_sys = BuffSystem(world.event_stream, world.hook_registry)

    for sys in (turn_sys, dmg_sys, heal_sys, hlth_sys, nrg_sys, buff_sys):
        world.systems.append(sys)

    hlth_sys.subscribe_to_events()
    nrg_sys.auto_recover_on_turn = False
    nrg_sys.subscribe_to_events()
    buff_sys.subscribe_to_events()

    seele = make_seele(version)
    enemy1 = make_enemy(version)
    enemy2 = make_enemy(version)
    entities = [("Seele", seele), ("Enemy #1", enemy1), ("Enemy #2", enemy2)]

    context = SkillContext(
        world=world,
        event_bus=world.event_stream,
        hook_chain=world.hook_registry,
    )
    fake_char = _FakeUserChar(
        char_config_id=SEELE_CONFIG_ID,
        version=version,
        eidolon_level=4,
    )
    bundle = CharacterSkillLoader(config_loader).load_for_character(
        fake_char, context, activated_bonus_ability_ids=set()
    )
    console.print(
        "[green]+ Loaded "
        + str(len(bundle.all))
        + " scripts ("
        + str(len(bundle.eidolons))
        + " eidolons)[/]"
    )
    console.print(
        "  Eidolons: " + ", ".join(type(e).__name__ for e in bundle.eidolons)
    )

    seele_skill_script = bundle.active[1]
    seele_ultimate_script = bundle.active[2]
    talent_script = bundle.talents[0] if bundle.talents else None

    if talent_script:
        console.print(
            "  [green]Talent: "
            + type(talent_script).__name__
            + " (Resurgence +80% DMG)[/]"
        )
    console.print(
        "  [green]Ultimate: " + type(seele_ultimate_script).__name__ + "[/]"
    )

    enemy_cfg = config_loader.get_enemy_config("mara_struck_soldier", version)[
        "config"
    ]
    passive_cfg = enemy_cfg.passives[0]
    for eid in (enemy1, enemy2):
        obj = SkillScriptLoader().load_passive(
            version=version,
            enemy_name="mara_struck_soldier",
            script=passive_cfg.script,
            context=context,
        )
        obj.activate()
    console.print("[green]+ Enemy passive: " + passive_cfg.name + "[/]\n")

    def _on_revived(event):
        data = event.data if hasattr(event, "data") else event
        eid = data.get("entity_id") if isinstance(data, dict) else None
        if eid is not None:
            turn_sys.on_character_knocked_down_restored(eid)

    def _on_knocked_down(event):
        data = event.data if hasattr(event, "data") else event
        eid = data.get("entity_id") if isinstance(data, dict) else None
        if eid is not None:
            turn_sys.on_character_knocked_down(eid)

    world.event_stream.subscribe(
        EventType.CHARACTER_KNOCKED_DOWN_RESTORED,
        _on_revived,
        priority=60,
        owner="test_revive_sync",
    )
    world.event_stream.subscribe(
        EventType.CHARACTER_KNOCKED_DOWN,
        _on_knocked_down,
        priority=60,
        owner="test_knockdown_sync",
    )

    turn_sys.initialize()
    console.print("[green]+ Turn system ready[/]\n")

    console.print(
        render_action_bar(entities, turn_sys.current_actor_id, turn_sys)
    )
    console.print(render_skill_point_bar(seele))
    console.print()

    def _try_fire_ultimate() -> bool:
        """If Seele has full energy, fire ultimate immediately (cut-in)."""
        seele_en = esper.component_for_entity(seele, StandardEnergyComponent)
        if seele_en.energy < seele_en.max_energy:
            return False

        target = next(
            (eid for _, eid in entities if eid != seele and alive(eid)),
            None,
        )
        if target is None:
            return False

        target_label = next(lbl for lbl, eid in entities if eid == target)
        tgt_hp = esper.component_for_entity(target, HealthComponent)
        hp_before = tgt_hp.value

        console.print(
            "\n[bold magenta]*** ULTIMATE: Seele -> " + target_label + " ***[/]"
        )

        result = seele_ultimate_script.execute(seele, [target])
        base_dmg = result.get("base_damage", 0)
        dmg_sys.calculate_and_apply_damage(
            attacker_id=seele,
            defender_id=target,
            base_damage=base_dmg,
            damage_type="quantum",
        )

        hp_after = esper.component_for_entity(target, HealthComponent).value
        dmg_dealt = hp_before - hp_after
        console.print("  [bold red]Ult DMG: " + f"{dmg_dealt:.0f}" + "[/]")
        console.print(
            "  "
            + target_label
            + " HP: "
            + f"{hp_before:.0f} -> {max(hp_after, 0):.0f}"
        )

        seele_en.energy = 0
        console.print("  [magenta]Energy: 120 -> 0[/]")

        if hp_after <= 0 and talent_script is not None:
            talent_script.resurgence_active = True
            talent_script.resurgence_entity = seele

        if hp_after <= 0 and alive(target):
            console.print(
                "[bold yellow]"
                + target_label
                + " revived (Rejuvenate: 50% HP)![/]"
            )

        console.print()
        console.print(make_status_table(entities))
        return True

    turn = 0
    while True:
        _try_fire_ultimate()

        actor = turn_sys.current_actor_id
        if actor is None:
            console.print("[red]x No current actor -- stall[/]")
            break

        label = next(
            (lbl for lbl, eid in entities if eid == actor), f"Entity#{actor}"
        )

        turn += 1
        console.print(
            "\n[bold cyan]"
            + ("=" * 6)
            + " Turn "
            + str(turn)
            + ("=" * 6)
            + "[/]"
        )
        console.print(render_action_bar(entities, actor, turn_sys))
        console.print(render_skill_point_bar(seele))

        if actor == seele:
            while True:
                target = next(
                    (eid for _, eid in entities if eid != seele and alive(eid)),
                    None,
                )
                if target is None:
                    console.print("[green]* No enemies remain[/]")
                    break

                target_label = next(
                    lbl for lbl, eid in entities if eid == target
                )

                resurg = (
                    talent_script is not None
                    and talent_script.consume_resurgence(seele)
                )
                hp_before, hp_after = execute_seele_action(
                    seele,
                    target,
                    target_label,
                    seele_skill_script,
                    dmg_sys,
                    resurgence_active=resurg,
                    console=console,
                )

                if hp_after <= 0:
                    seele_en = esper.try_component(
                        seele, StandardEnergyComponent
                    )
                    if seele_en:
                        console.print(
                            "  [magenta]Energy: "
                            + f"{seele_en.energy:.0f}"
                            + "/"
                            + f"{seele_en.max_energy:.0f}"
                            + "  (E4 +15 on kill)[/]"
                        )
                    if alive(target):
                        console.print(
                            "[bold yellow]"
                            + target_label
                            + " revived (Rejuvenate: 50% HP)![/]"
                        )

                if (
                    talent_script is not None
                    and talent_script.resurgence_active
                ):
                    console.print(
                        "  [bold magenta]>>> Resurgence triggered![/]"
                    )
                    continue
                break

            if target is None:
                break
        else:
            if not alive(seele):
                console.print(
                    "\n[bold yellow]> "
                    + label
                    + "[/] -- [dim]Seele down, skip[/]"
                )
                turn_sys.on_action_finished()
                continue

            console.print(
                "\n[bold yellow]> "
                + label
                + "[/] -- [bold]Basic Attack[/] -> Seele"
            )
            enemy_atk = esper.component_for_entity(actor, AttackComponent).value
            seele_hp_before = esper.component_for_entity(
                seele, HealthComponent
            ).value

            dmg_sys.calculate_and_apply_damage(
                attacker_id=actor,
                defender_id=seele,
                base_damage=enemy_atk * 1.0,
                damage_type="physical",
            )

            seele_hp_after = esper.component_for_entity(
                seele, HealthComponent
            ).value
            actual = seele_hp_before - seele_hp_after
            console.print("  [red]Physical DMG: " + f"{actual:.0f}" + "[/]")
            console.print(
                "  Seele HP: "
                + f"{seele_hp_before:.0f}"
                + " -> "
                + f"{max(seele_hp_after, 0):.0f}"
            )
            if seele_hp_after <= 0:
                console.print("  [bold red]Seele knocked down![/]")

            seele_en = esper.try_component(seele, StandardEnergyComponent)
            if seele_en:
                console.print(
                    "  [dim]Energy: "
                    + f"{seele_en.energy:.0f}"
                    + "/"
                    + f"{seele_en.max_energy:.0f}"
                    + "  (hit +5)[/dim]"
                )

        console.print()
        console.print(make_status_table(entities))

        turn_sys.on_action_finished()

        if not alive(seele):
            console.print(
                Panel("[bold red]x Seele defeated![/]", box=box.ROUNDED)
            )
            break

        enemies_alive = [
            eid for _, eid in entities if eid != seele and alive(eid)
        ]
        if not enemies_alive:
            console.print(Panel("[bold green]* Victory![/]", box=box.ROUNDED))
            break

    console.print(
        "\n[bold cyan]"
        + ("=" * 6)
        + " Summary ("
        + str(turn)
        + " turns)"
        + ("=" * 6)
        + "[/]"
    )
    console.print(make_status_table(entities))

    spd = esper.try_component(seele, SpeedComponent)
    stack = esper.try_component(seele, StackComponent)
    en = esper.try_component(seele, StandardEnergyComponent)
    console.print("\n[bold]Seele final stats:[/]")
    if spd:
        stack_str = str(stack.current) + "/" + str(stack.max) if stack else "?"
        console.print(
            "  SPD: "
            + f"{spd.final_speed:.1f}"
            + "  (stacks: "
            + stack_str
            + ")"
        )
    if en:
        console.print(
            "  Energy: " + f"{en.energy:.0f}" + "/" + f"{en.max_energy:.0f}"
        )

    console.print(
        "\n[dim]Mechanics: SKILL(SPD+25%, quantum dmg)  "
        "E1(crit+15% vs HP<=80%)  E2(2 stacks)  "
        "E4(+15 energy on kill)  ULT(cut-in, 4x ATK)  "
        "Talent(Resurgence: +80% DMG extra action)  "
        "Rejuvenate(50% HP revive x1)[/]"
    )

    world.deactivate()
    try:
        esper.switch_world("default")
    except (KeyError, ValueError):
        pass


if __name__ == "__main__":
    main()
