"""BattleController -- bridges ECS battle logic and the TUI."""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass, field
from typing import cast

import esper

from hsr_sim.ecs.components import (
    AttackComponent,
    BuffContainerComponent,
    CharacterIdentityComponent,
    CharacterStatusComponent,
    CritDamageComponent,
    CritRateComponent,
    DefenseComponent,
    HealthComponent,
    ShieldComponent,
    SkillPointComponent,
    SpeedComponent,
    StackComponent,
    StandardEnergyComponent,
)
from hsr_sim.ecs.systems import (
    BuffSystem,
    DamageSystem,
    EnergySystem,
    HealingSystem,
    HealthSystem,
    TurnSystem,
)
from hsr_sim.ecs.world import ECSWorld
from hsr_sim.events.types import EventType
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.services import config_loader
from hsr_sim.skills.script_loader import (
    CharacterSkillLoader,
    SkillContext,
)
from .widgets.selector_rules import TargetInfo

SEELE_CONFIG_ID = 10000000
SPD_BUFF_AMOUNT = 25.0
STACK_TYPE = "seele_spd_boost"
SKILL_SP_COST = 1
BASIC_SP_GAIN = 1
MAX_SP = 5
BASIC_DMG_MULTIPLIER = 1.0


@dataclass
class BattleSnapshot:
    """Immutable snapshot of battle state for TUI rendering."""

    characters: list[dict] = field(default_factory=list)
    enemies: list[dict] = field(default_factory=list)
    action_bar_entries: list[tuple[int, str, float, float, bool]] = field(
        default_factory=list
    )
    current_actor_id: int | None = None
    skill_point_current: int = 0
    skill_point_max: int = 0
    is_player_turn: bool = False
    enemy_targets: list[TargetInfo] = field(default_factory=list)
    ally_targets: list[TargetInfo] = field(default_factory=list)
    log_messages: list[tuple[str, str]] = field(default_factory=list)
    is_battle_over: bool = False
    victory: bool = False
    needs_input: bool = False


@dataclasses.dataclass
class _FakeUserChar:
    char_config_id: int
    version: str
    eidolon_level: int = 0


class BattleController:
    """Manages ECS battle state and provides snapshots for TUI rendering."""

    def __init__(self, version: str = "v1.0") -> None:
        self.version = version
        self.world: ECSWorld | None = None
        self.seele_id: int = 0
        self.enemy_ids: list[int] = []
        self.turn_sys: TurnSystem | None = None
        self.dmg_sys: DamageSystem | None = None
        self.bundle = None
        self.seele_skill = None
        self.seele_ultimate = None
        self.talent_script = None
        self.context: SkillContext | None = None
        self._log: list[tuple[str, str]] = []
        self._pending_resurgence = False
        self._seed: int = 42

    # ── Lifecycle ─────────────────────────────────────

    def start_battle(self, seed: int | None = None) -> BattleSnapshot:
        """Initialize battle and return initial snapshot."""
        if seed is not None:
            self._seed = seed
        random.seed(self._seed)

        self._log = []
        self._log_msg("green", f"Battle initialized (seed={self._seed})")

        self._init_world()
        self._init_systems()
        self._create_entities()
        self._load_skills()
        self._register_event_handlers()

        assert self.turn_sys is not None
        self.turn_sys.initialize()
        self._log_msg("green", "Turn system ready")

        return self._take_snapshot(needs_input=self._is_seele_turn())

    def cleanup(self) -> None:
        """Deactivate ECS world."""
        if self.world is not None:
            self.world.deactivate()
        try:
            esper.switch_world("default")
        except (KeyError, ValueError):
            pass

    # ── Turn execution ────────────────────────────────

    def player_basic_attack(self, target_id: int) -> BattleSnapshot:
        """Player uses basic attack on target (q key)."""
        return self._execute_player_action(target_id, use_skill=False)

    def player_skill(self, target_id: int) -> BattleSnapshot:
        """Player uses skill on target (e key). Requires SP."""
        return self._execute_player_action(target_id, use_skill=True)

    def _execute_player_action(
        self, target_id: int, use_skill: bool
    ) -> BattleSnapshot:
        """Core player action logic: basic attack or skill on target."""
        assert self.turn_sys is not None
        if not self._is_seele_turn():
            self._log_msg("dim", "Not Seele's turn")
            return self._take_snapshot()

        if target_id not in self.enemy_ids or not self._is_alive(target_id):
            self._log_msg("dim", f"Invalid/dead target: {target_id}")
            return self._take_snapshot(needs_input=True)

        if use_skill:
            sp = esper.try_component(self.seele_id, SkillPointComponent)
            if sp is None or sp.current < SKILL_SP_COST:
                self._log_msg("dim", "Not enough SP! Use basic attack (q).")
                return self._take_snapshot(needs_input=True)

        target_label = self._entity_label(target_id)
        resurgence = self._consume_resurgence()

        hp_before = self._enemy_hp(target_id)

        if use_skill:
            self._execute_skill(target_id, target_label, resurgence)
        else:
            self._execute_basic(target_id, target_label, resurgence)

        hp_after = self._enemy_hp(target_id)
        dmg = hp_before - hp_after
        self._log_msg("red", f"Quantum DMG: {dmg:.0f}")

        self._check_post_action(target_id, target_label, hp_after)

        if self._talent_has_resurgence():
            self._log_msg("magenta bold", ">>> Resurgence triggered!")
            return self._take_snapshot(needs_input=True)

        self.turn_sys.on_action_finished()
        return self._take_snapshot(
            needs_input=self._is_seele_turn() and self._has_enemies_alive()
        )

    def advance_enemy_turn(self) -> BattleSnapshot:
        """Auto-execute enemy's turn."""
        assert self.turn_sys is not None
        assert self.dmg_sys is not None
        actor = self.turn_sys.current_actor_id
        if actor is None or actor == self.seele_id:
            return self._take_snapshot()

        label = self._entity_label(actor)
        self._log_msg("yellow", f"> {label} -- Basic Attack -> Seele")

        enemy_atk = esper.try_component(actor, AttackComponent)
        atk_value = enemy_atk.value if enemy_atk else 100.0

        seele_hp_before = self._char_hp(self.seele_id)

        self.dmg_sys.calculate_and_apply_damage(
            attacker_id=actor,
            defender_id=self.seele_id,
            base_damage=atk_value * 1.0,
            damage_type="physical",
        )

        seele_hp_after = self._char_hp(self.seele_id)
        actual = seele_hp_before - seele_hp_after
        self._log_msg("red", f"Physical DMG: {actual:.0f}")

        if seele_hp_after <= 0:
            self._log_msg("bold red", "Seele knocked down!")

        self.turn_sys.on_action_finished()
        return self._take_snapshot(
            needs_input=self._is_seele_turn() and self._has_enemies_alive()
        )

    def try_fire_ultimate(
        self, target_id: int | None = None
    ) -> BattleSnapshot:
        """If Seele has full energy, fire ultimate on given or first alive enemy."""
        assert self.seele_ultimate is not None
        assert self.dmg_sys is not None
        seele_en = esper.try_component(self.seele_id, StandardEnergyComponent)
        if not seele_en or seele_en.energy < seele_en.max_energy:
            return self._take_snapshot()

        target = (
            target_id
            if target_id is not None and self._is_alive(target_id)
            else self._find_alive_enemy()
        )
        if target is None:
            return self._take_snapshot()

        target_label = self._entity_label(target)
        hp_before = self._enemy_hp(target)

        self._log_msg("bold magenta", f"*** ULTIMATE: Seele -> {target_label} ***")

        result = self.seele_ultimate.execute(self.seele_id, [target])
        base_dmg = result.get("base_damage", 0)
        self.dmg_sys.calculate_and_apply_damage(
            attacker_id=self.seele_id,
            defender_id=target,
            base_damage=base_dmg,
            damage_type="quantum",
        )

        hp_after = self._enemy_hp(target)
        dmg = hp_before - hp_after
        self._log_msg("bold red", f"Ult DMG: {dmg:.0f}")

        seele_en.energy = 0
        self._log_msg("magenta", "Energy: 120 -> 0")

        self._check_post_action(target, target_label, hp_after)
        return self._take_snapshot(
            needs_input=self._is_seele_turn() and self._has_enemies_alive()
        )

    def can_ultimate(self) -> bool:
        """Check if Seele can fire ultimate right now."""
        seele_en = esper.try_component(self.seele_id, StandardEnergyComponent)
        return seele_en is not None and seele_en.energy >= seele_en.max_energy

    def has_resurgence(self) -> bool:
        """Check if Seele's talent resurgence is active."""
        return self._talent_has_resurgence()

    # ── Snapshot ──────────────────────────────────────

    def _take_snapshot(
        self,
        needs_input: bool = False,
    ) -> BattleSnapshot:
        """Read current ECS state into a snapshot."""
        assert self.turn_sys is not None
        # Characters
        characters = []
        for label, eid in [("Seele", self.seele_id)]:
            hp = esper.try_component(eid, HealthComponent)
            energy = esper.try_component(eid, StandardEnergyComponent)
            shield = esper.try_component(eid, ShieldComponent)

            stacks = self._get_stacks(eid)
            buffs = self._get_buffs(eid)

            characters.append({
                "name": label,
                "hp": hp.value if hp else 0,
                "max_hp": hp.max_value if hp else 100,
                "shield": shield.value if shield else 0,
                "energy": energy.energy if energy else 0,
                "max_energy": energy.max_energy if energy else 120,
                "stacks": stacks,
                "buffs": buffs,
                "energy_key": 1,
                "is_current_actor": eid == self.turn_sys.current_actor_id,
                "is_alive": self._is_alive(eid),
            })

        # Pad to 4 characters
        while len(characters) < 4:
            characters.append({
                "name": "",
                "hp": 0,
                "max_hp": 100,
                "shield": 0,
                "energy": 0,
                "max_energy": 120,
                "stacks": [],
                "buffs": [],
                "energy_key": len(characters) + 1,
                "is_current_actor": False,
                "is_alive": False,
            })

        alive_enemy_ids = [
            eid for eid in self.enemy_ids if self._is_alive(eid)
        ]

        # Enemies (dead enemies are removed from TUI)
        enemies = []
        for eid in alive_enemy_ids:
            hp = esper.try_component(eid, HealthComponent)
            enemies.append({
                "name": self._entity_label(eid),
                "hp": hp.value if hp else 0,
                "max_hp": hp.max_value if hp else 100,
                "toughness": 0,
                "max_toughness": 0,
                "toughness_locked": False,
                "weakness_types": [],
                "weakness_disabled": False,
                "buffs": [],
                "special_stacks": "",
            })

        # Action bar
        action_entries = self._build_action_entries()

        # SP
        sp = esper.try_component(self.seele_id, SkillPointComponent)

        # Targets for selector (dead enemies are removed)
        enemy_targets = [
            TargetInfo(
                entity_id=eid,
                label=self._entity_label(eid),
                is_enemy=True,
                is_alive=True,
            )
            for eid in alive_enemy_ids
        ]

        ally_targets = [
            TargetInfo(
                entity_id=self.seele_id,
                label="Seele",
                is_enemy=False,
                is_alive=self._is_alive(self.seele_id),
            ),
        ]
        while len(ally_targets) < 4:
            ally_targets.append(
                TargetInfo(
                    entity_id=1000 + len(ally_targets),
                    label="---",
                    is_enemy=False,
                    is_alive=False,
                )
            )

        # Battle over check
        is_battle_over = False
        victory = False
        if not self._is_alive(self.seele_id):
            is_battle_over = True
            victory = False
        elif self._all_enemies_dead():
            is_battle_over = True
            victory = True

        log = self._log[:]
        self._log.clear()

        return BattleSnapshot(
            characters=characters,
            enemies=enemies,
            action_bar_entries=action_entries,
            current_actor_id=self.turn_sys.current_actor_id,
            skill_point_current=sp.current if sp else 0,
            skill_point_max=sp.max_value if sp else 5,
            is_player_turn=self._is_seele_turn(),
            enemy_targets=enemy_targets,
            ally_targets=ally_targets,
            log_messages=log,
            is_battle_over=is_battle_over,
            victory=victory,
            needs_input=needs_input and not is_battle_over,
        )

    # ── Private: init ─────────────────────────────────

    def _init_world(self) -> None:
        self.world = ECSWorld(self.version)
        esper.switch_world(self.world.world_name)
        self.world.activate()

    def _init_systems(self) -> None:
        assert self.world is not None
        self.turn_sys = TurnSystem(self.world.event_stream)
        self.dmg_sys = DamageSystem(
            self.world.event_stream,
            self.world.hook_registry,
            lambda: 0,
        )
        heal_sys = HealingSystem(
            self.world.event_stream,
            self.world.hook_registry,
            lambda: 0,
        )
        hlth_sys = HealthSystem(
            self.world.event_stream,
            self.world.hook_registry,
        )
        nrg_sys = EnergySystem(self.world.event_stream)
        buff_sys = BuffSystem(
            self.world.event_stream,
            self.world.hook_registry,
        )

        for sys in (self.turn_sys, self.dmg_sys, heal_sys, hlth_sys, nrg_sys, buff_sys):
            self.world.systems.append(sys)

        hlth_sys.subscribe_to_events()
        nrg_sys.auto_recover_on_turn = False
        nrg_sys.subscribe_to_events()
        buff_sys.subscribe_to_events()

    def _create_entities(self) -> None:
        self.seele_id = self._make_seele()
        self.enemy_ids = [self._make_enemy() for _ in range(2)]

    def _make_seele(self) -> int:
        seele_data = config_loader.get_character("seele", self.version)
        assert seele_data is not None
        seele_cfg = seele_data["config"]
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
                version=self.version,
            ),
        )
        return e

    def _make_enemy(self) -> int:
        enemy_data = config_loader.get_enemy_config(
            "mara_struck_soldier", self.version
        )
        assert enemy_data is not None
        cfg = enemy_data["config"]
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

    def _load_skills(self) -> None:
        assert self.world is not None
        self.context = SkillContext(
            world=self.world,
            event_bus=self.world.event_stream,
            hook_chain=self.world.hook_registry,
        )
        fake_char = _FakeUserChar(
            char_config_id=SEELE_CONFIG_ID,
            version=self.version,
            eidolon_level=4,
        )
        self.bundle = CharacterSkillLoader(config_loader).load_for_character(
            cast(UserCharacter, fake_char),
            self.context,
            activated_bonus_ability_ids=set(),
        )
        n_scripts = len(self.bundle.all)
        n_eidolons = len(self.bundle.eidolons)
        self._log_msg(
            "green",
            f"Loaded {n_scripts} scripts ({n_eidolons} eidolons)",
        )

        self.seele_skill = self.bundle.active[1]
        self.seele_ultimate = self.bundle.active[2]
        self.talent_script = (
            self.bundle.talents[0] if self.bundle.talents else None
        )

        # Load enemy passives
        enemy_data = config_loader.get_enemy_config(
            "mara_struck_soldier", self.version
        )
        assert enemy_data is not None
        enemy_cfg = enemy_data["config"]
        from hsr_sim.skills.script_loader import SkillScriptLoader

        passive_cfg = enemy_cfg.passives[0]
        obj = SkillScriptLoader().load_passive(
            version=self.version,
            enemy_name="mara_struck_soldier",
            script=passive_cfg.script,
            context=self.context,
        )
        obj.activate()
        self._log_msg("green", f"Enemy passive: {passive_cfg.name}")

    def _register_event_handlers(self) -> None:
        assert self.world is not None
        assert self.turn_sys is not None
        turn_sys = self.turn_sys
        world = self.world

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
            owner="tui_revive_sync",
        )
        world.event_stream.subscribe(
            EventType.CHARACTER_KNOCKED_DOWN_RESTORED,
            _on_revived,
            priority=60,
            owner="tui_revive_sync",
        )
        world.event_stream.subscribe(
            EventType.CHARACTER_KNOCKED_DOWN,
            _on_knocked_down,
            priority=60,
            owner="tui_knockdown_sync",
        )

    # ── Private: actions ──────────────────────────────

    def _execute_skill(
        self, target_id: int, target_label: str, resurgence: bool
    ) -> None:
        assert self.seele_skill is not None
        sp = esper.try_component(self.seele_id, SkillPointComponent)
        if sp is not None:
            sp.current -= SKILL_SP_COST

        suffix = " [Resurgence]" if resurgence else ""
        self._log_msg("bold yellow", f"> Seele -- Skill -> {target_label}{suffix}")

        self.seele_skill.execute(self.seele_id, [target_id])
        EnergySystem.recover_energy(self.seele_id, 30.0)

    def _execute_basic(
        self, target_id: int, target_label: str, resurgence: bool
    ) -> None:
        assert self.dmg_sys is not None
        sp = esper.try_component(self.seele_id, SkillPointComponent)
        if sp is not None:
            sp.current = min(sp.current + BASIC_SP_GAIN, sp.max_value)

        seele_atk = esper.try_component(self.seele_id, AttackComponent)
        atk_val = seele_atk.value if seele_atk else 100.0

        suffix = " [Resurgence]" if resurgence else ""
        self._log_msg(
            "bold yellow",
            f"> Seele -- Basic Attack -> {target_label}{suffix}",
        )

        self.dmg_sys.calculate_and_apply_damage(
            attacker_id=self.seele_id,
            defender_id=target_id,
            base_damage=atk_val * BASIC_DMG_MULTIPLIER,
            damage_type="quantum",
        )
        EnergySystem.recover_energy(self.seele_id, 20.0)

    def _check_post_action(
        self, target_id: int, target_label: str, hp_after: float
    ) -> None:
        """After damaging an enemy, check for kill effects."""
        if hp_after <= 0:
            seele_en = esper.try_component(self.seele_id, StandardEnergyComponent)
            if seele_en:
                self._log_msg(
                    "magenta",
                    f"Energy: {seele_en.energy:.0f}/{seele_en.max_energy:.0f} (E4 +15 on kill)",
                )
            if self._is_alive(target_id):
                self._log_msg(
                    "bold yellow",
                    f"{target_label} revived (Rejuvenate: 50% HP)!",
                )

            # Check resurgence trigger
            if self.talent_script is not None and hp_after <= 0:
                self.talent_script.resurgence_active = True
                self.talent_script.resurgence_entity = self.seele_id

    # ── Private: helpers ──────────────────────────────

    def _is_seele_turn(self) -> bool:
        assert self.turn_sys is not None
        return self.turn_sys.current_actor_id == self.seele_id

    def _is_alive(self, entity_id: int) -> bool:
        s = esper.try_component(entity_id, CharacterStatusComponent)
        return s is not None and s.status == CharacterStatus.ALIVE

    def _has_enemies_alive(self) -> bool:
        return any(self._is_alive(eid) for eid in self.enemy_ids)

    def _all_enemies_dead(self) -> bool:
        return not self._has_enemies_alive()

    def _find_alive_enemy(self) -> int | None:
        for eid in self.enemy_ids:
            if self._is_alive(eid):
                return eid
        return None

    def _entity_label(self, entity_id: int) -> str:
        if entity_id == self.seele_id:
            return "Seele"
        for i, eid in enumerate(self.enemy_ids):
            if eid == entity_id:
                return f"Enemy #{i + 1}"
        return f"Entity#{entity_id}"

    def _char_hp(self, entity_id: int) -> float:
        hp = esper.try_component(entity_id, HealthComponent)
        return hp.value if hp else 0

    def _enemy_hp(self, entity_id: int) -> float:
        return self._char_hp(entity_id)

    def _get_stacks(self, entity_id: int) -> list[tuple[str, int, int]]:
        stack = esper.try_component(entity_id, StackComponent)
        if stack is not None:
            return [(stack.stack_type, stack.current, stack.max)]
        return []

    def _get_buffs(self, entity_id: int) -> list[tuple[str, int]]:
        return []

    def _consume_resurgence(self) -> bool:
        if self.talent_script is None:
            return False
        return self.talent_script.consume_resurgence(self.seele_id)

    def _talent_has_resurgence(self) -> bool:
        if self.talent_script is None:
            return False
        return self.talent_script.resurgence_active

    def _build_action_entries(
        self,
    ) -> list[tuple[int, str, float, float, bool]]:
        if self.turn_sys is None:
            return []
        entries = self.turn_sys.action_queue.sorted_entries()
        result = []
        for eid, av in entries:
            label = self._entity_label(eid)
            spd = esper.try_component(eid, SpeedComponent)
            speed = spd.final_speed if spd else 0
            is_enemy = eid != self.seele_id
            result.append((eid, label, av, speed, is_enemy))
        return result

    def _log_msg(self, style: str, msg: str) -> None:
        self._log.append((style, msg))
