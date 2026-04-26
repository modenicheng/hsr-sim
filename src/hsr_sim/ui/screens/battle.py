"""BattleScreen -- main TUI battle view composing all battle widgets."""

from __future__ import annotations

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Container, Grid, Horizontal
from textual.message import Message
from textual.screen import Screen
from textual.widgets import RichLog, Static

import time

from ..battle_controller import BattleController, BattleSnapshot
from hsr_sim.ecs.components import (
    AttackComponent,
    CharacterStatusComponent,
    CritDamageComponent,
    CritRateComponent,
    DefenseComponent,
    HealthComponent,
    SpeedComponent,
    StandardEnergyComponent,
)
from ..widgets.action_bar import ActionBarWidget
from ..widgets.action_buffer import ActionBufferWidget
from ..widgets.boss_widget import BossWidget
from ..widgets.character_widget import CharacterWidget
from ..widgets.enemy_widget import EnemyWidget
from ..widgets.selector_rules import (
    SelectorRule,
    SingleTargetRule,
    TargetInfo,
)
from ..widgets.skill_point_widget import SkillPointWidget
from ..widgets.status_dialog import StatusDialog
from ..widgets.target_selector import ArrowState, TargetSelector
from ..widgets.turn_spinner import TurnSpinnerWidget

_MAX_ENEMIES = 5
_MAX_CHARS = 4
_ENEMY_ADVANCE_DELAY = 0.7


class CompactButton(Static):
    """A compact clickable button (not Textual's default Button)."""

    DEFAULT_CSS = """
    CompactButton {
        width: auto;
        height: 1;
        padding: 0 2;
        background: $surface;
        color: white;
    }
    CompactButton:hover {
        background: $accent;
        color: $text;
    }
    """

    def __init__(self, label: str, id: str | None = None) -> None:
        super().__init__(label, id=id)

    def on_click(self) -> None:
        self.post_message(self.Pressed(self))

    class Pressed(Message):
        """Emitted when button is clicked."""

        def __init__(self, button: CompactButton) -> None:
            super().__init__()
            self.button = button


class BattleScreen(Screen[None]):
    """Main battle screen.

    Layout:
        #boss-section     (auto, hidden by default) -- BOSS HP area
        #body             (1fr, grid: 22 | 1fr)
          #action-column  (22) -- action bar + status buttons below
          #main-area      (1fr) -- enemy / selector / ally / log
    """

    DEFAULT_CSS = """
    BattleScreen {
        layout: vertical;
        overflow-y: hidden;
    }

    #boss-section {
        width: 100%;
        height: auto;
    }

    #boss-section.section-hidden {
        display: none;
    }

    #boss-section Center {
        height: auto;
    }

    #boss-section BossWidget {
        margin-bottom: 0;
    }

    #boss-section ActionBufferWidget {
        width: auto;
        height: 1;
    }

    #body {
        width: 100%;
        height: 1fr;
        layout: grid;
        grid-size: 2;
        grid-columns: 22 1fr;
        grid-rows: 1fr;
    }

    #action-column {
        height: 100%;
        padding: 0 1;
        border-right: solid $surface;
        overflow-y: auto;
        scrollbar-size: 0 0;
    }

    #status-buttons {
        dock: bottom;
        layout: vertical;
        width: 100%;
        height: auto;
        padding-bottom: 1;
    }

    #status-buttons CompactButton {
        width: 100%;
    }

    #main-area {
        height: 1fr;
        width: 100%;
        layout: vertical;
    }

    #enemy-parent {
        width: 100%;
        height: 1fr;
        layout: vertical;
        align: center top;
    }

    #enemy-section {
        width: 100%;
        height: auto;
    }

    #enemy-grid {
        width: 100%;
        height: auto;
    }

    #selector-section {
        width: 100%;
        height: auto;
        layout: vertical;
        align: center middle;
    }

    #selector-e {
        width: 100%;
        height: 1;
    }

    #selector-e > Static {
        width: 100%;
        height: 1;
        content-align: center middle;
    }

    #selector-a {
        width: 100%;
        height: 2;
        margin-top: 1;
    }

    #selector-a > Static {
        width: 100%;
        height: 1;
        content-align: center middle;
    }

    #ally-row {
        width: 100%;
        height: auto;
    }

    #ally-row > #char-panel {
        width: 1fr;
        height: auto;
        padding: 0 2;
    }

    #sp-column {
        width: 10;
        height: auto;
        margin-top: 1;
    }

    #sp-column > SkillPointWidget {
        width: 100%;
        height: auto;
        margin-left: 2;
    }

    #sp-column > TurnSpinnerWidget {
        width: 100%;
        height: 1;
        margin-top: 1;
    }

    #ally-parent {
        width: 100%;
        height: 1fr;
        layout: vertical;
        align: center bottom;
    }

    #char-panel > CharacterWidget {
        width: 100%;
    }

    #battle-log {
        width: 100%;
        height: auto;
        max-height: 8;
        border-top: solid $surface;
    }

    #battle-log RichLog {
        width: 100%;
        height: auto;
        max-height: 8;
        min-height: 1;
    }

    #battle-over-panel {
        background: $panel;
        color: $text;
        padding: 1 3;
        width: auto;
        height: auto;
        dock: top;
        layer: overlay;
    }
    """

    BINDINGS = [
        ("escape", "maybe_quit", ""),
        ("q", "basic_attack", "普攻"),
        ("e", "skill", "战技"),
        ("a", "cursor_left", "←"),
        ("d", "cursor_right", "→"),
        ("c", "show_char_status", "角色"),
        ("z", "show_enemy_status", "敌方"),
        ("1", "ultimate(1)", "终1"),
        ("2", "ultimate(2)", "终2"),
        ("3", "ultimate(3)", "终3"),
        ("4", "ultimate(4)", "终4"),
    ]

    class TargetSelected(Message):
        """Emitted when user selects a target."""

        def __init__(self, target_id: int) -> None:
            super().__init__()
            self.target_id = target_id

    class QuitBattle(Message):
        """Emitted when user wants to quit the battle."""

    # ── Lifecycle ───────────────────────────────────

    def compose(self) -> ComposeResult:
        # Top: BOSS HP area (hidden by default)
        with Container(id="boss-section", classes="section-hidden"):
            with Center():
                yield BossWidget(id="boss")
            with Center():
                yield ActionBufferWidget(id="action-buffer")

        # Body grid: action column | main area
        with Grid(id="body"):
            with Container(id="action-column"):
                yield ActionBarWidget(id="action-bar")
                with Container(id="status-buttons"):
                    yield CompactButton("角色状态", id="btn-char-status")
                    yield CompactButton("敌方状态", id="btn-enemy-status")
            with Container(id="main-area"):
                with Container(id="enemy-parent"):
                    with Container(id="enemy-section"):
                        with Grid(id="enemy-grid"):
                            for i in range(1, _MAX_ENEMIES + 1):
                                yield EnemyWidget(id=f"enemy-{i}")
                    with Grid(id="selector-e"):
                        for i in range(_MAX_ENEMIES):
                            yield Static("", id=f"sel-e-{i}")
                with Container(id="selector-section"):
                    with Grid(id="selector-a"):
                        for i in range(_MAX_CHARS):
                            yield Static("", id=f"sel-a-{i}")
                with Container(id="ally-parent"):
                    with Horizontal(id="ally-row"):
                        with Grid(id="char-panel"):
                            for i in range(1, _MAX_CHARS + 1):
                                yield CharacterWidget(id=f"char-{i}")
                        with Container(id="sp-column"):
                            yield SkillPointWidget(id="sp-widget")
                            yield TurnSpinnerWidget(
                                id="turn-spinner", is_player_turn=True
                            )
                with Container(id="battle-log"):
                    yield RichLog(id="log", highlight=True, markup=True)

    def on_mount(self) -> None:
        self._selector = TargetSelector()
        self._battle_over_shown = False
        self._last_esc_press: float | None = None

        # Ensure grid+selector containers have correct layout properties.
        cols5 = "1fr 1fr 1fr 1fr 1fr"
        self.query_one("#enemy-grid").set_styles(
            f"grid-size: 5; grid-columns: {cols5};"
        )
        self.query_one("#selector-e").set_styles(
            f"grid-size: 5; grid-columns: {cols5};"
        )
        self.query_one("#selector-a").set_styles(
            "grid-size: 4; grid-columns: 1fr 1fr 1fr 1fr;"
        )
        self.query_one("#char-panel").set_styles(
            "grid-size: 4; grid-columns: 1fr 1fr 1fr 1fr;"
        )

        self._controller = BattleController(version="v1.0")
        snapshot = self._controller.start_battle()
        self._refresh_from_snapshot(snapshot)

        if not snapshot.is_battle_over:
            self._handle_snapshot_flow(snapshot)

    # ── Message handlers ────────────────────────────

    def on_battle_screen_target_selected(
        self, event: BattleScreen.TargetSelected
    ) -> None:
        if self._controller is None:
            return
        if self._battle_over_shown or not self._controller._has_enemies_alive():
            return

        target_id = event.target_id

        snapshot = self._controller.player_basic_attack(target_id)
        self._refresh_from_snapshot(snapshot)

        if snapshot.is_battle_over:
            self._show_battle_over(snapshot)
            return

        self._handle_snapshot_flow(snapshot)

    def on_battle_screen_quit_battle(
        self, event: BattleScreen.QuitBattle
    ) -> None:
        self._cleanup()

    def on_compact_button_pressed(self, event: CompactButton.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-char-status":
            self.action_show_char_status()
        elif bid == "btn-enemy-status":
            self.action_show_enemy_status()

    # ── Public update API (used by _refresh_from_snapshot) ─

    def toggle_boss_section(self) -> None:
        section = self.query_one("#boss-section")
        if section.has_class("section-hidden"):
            section.remove_class("section-hidden")
        else:
            section.add_class("section-hidden")

    def update_boss(
        self,
        name: str,
        hp: float,
        max_hp: float,
        toughness: int | None = None,
        max_toughness: int | None = None,
        toughness_locked: bool = False,
        weakness_types: list[str] | None = None,
        weakness_disabled: bool = False,
        buffs: list[tuple[str, int]] | None = None,
        special_stacks: str | None = None,
    ) -> None:
        boss = self.query_one("#boss", BossWidget)
        boss.update_state(
            name=name,
            hp=hp,
            max_hp=max_hp,
            toughness=toughness if toughness is not None else 0,
            max_toughness=max_toughness if max_toughness is not None else 0,
            toughness_locked=toughness_locked,
            weakness_types=weakness_types or [],
            weakness_disabled=weakness_disabled,
            buffs=buffs or [],
            special_stacks=special_stacks,
        )

    def update_enemies(self, enemies: list[dict]) -> None:
        grid = self.query_one("#enemy-grid", Grid)
        existing = list(grid.query(EnemyWidget))
        n = len(enemies)

        while len(existing) < n:
            w = EnemyWidget(id=f"enemy-{len(existing) + 1}")
            grid.mount(w)
            existing.append(w)
        while len(existing) > n:
            w = existing.pop()
            w.remove()

        for i, data in enumerate(enemies):
            existing[i].update_state(
                name=data.get("name", ""),
                hp=data.get("hp", 0),
                max_hp=data.get("max_hp", 100),
                toughness=data.get("toughness", 0),
                max_toughness=data.get("max_toughness", 0),
                toughness_locked=data.get("toughness_locked", False),
                weakness_types=data.get("weakness_types", []),
                weakness_disabled=data.get("weakness_disabled", False),
                buffs=data.get("buffs", []),
                special_stacks=data.get("special_stacks"),
            )

        self._resize_enemy_grid(n)

    def update_characters(self, characters: list[dict]) -> None:
        for i in range(1, _MAX_CHARS + 1):
            w = self.query_one(f"#char-{i}", CharacterWidget)
            if i <= len(characters):
                data = characters[i - 1]
                w.update_state(
                    name=data.get("name", ""),
                    hp=data.get("hp", 0),
                    max_hp=data.get("max_hp", 100),
                    shield=data.get("shield", 0),
                    energy=data.get("energy", 0),
                    max_energy=data.get("max_energy", 120),
                    stacks=data.get("stacks", []),
                    buffs=data.get("buffs", []),
                    energy_key=i,
                    is_current_actor=data.get("is_current_actor", False),
                    is_alive=data.get("is_alive", True),
                )
            else:
                w.update_state(
                    name="",
                    hp=0,
                    max_hp=100,
                    energy=0,
                    max_energy=120,
                    stacks=[],
                    buffs=[],
                    energy_key=i,
                    is_current_actor=False,
                    is_alive=False,
                )

    def update_skill_points(
        self,
        current: int | None = None,
        max_sp: int | None = None,
    ) -> None:
        w = self.query_one("#sp-widget", SkillPointWidget)
        w.update_sp(current=current, max_sp=max_sp)

    def update_turn_spinner(self, is_player_turn: bool) -> None:
        w = self.query_one("#turn-spinner", TurnSpinnerWidget)
        w.set_player_turn(is_player_turn)

    def update_action_bar(
        self,
        entries: list[tuple[int, str, float, float, bool]],
        current_actor: int | None = None,
    ) -> None:
        w = self.query_one("#action-bar", ActionBarWidget)
        w.update_entries(entries, current_actor)

    def update_action_buffer(self, actions: list[str]) -> None:
        w = self.query_one("#action-buffer", ActionBufferWidget)
        w.update_actions(actions)

    def setup_target_selector(
        self,
        targets: list[TargetInfo],
        primary_id: int | None = None,
        rule: SelectorRule | None = None,
    ) -> None:
        self._selector.update_targets(targets, primary_id, rule)
        self._refresh_arrows()

    # ── Actions / Bindings ──────────────────────────

    def action_maybe_quit(self) -> None:
        """Escape: once=notify, double-press (1.5s) = quit."""
        now = time.monotonic()
        if self._last_esc_press is not None and (now - self._last_esc_press) < 1.5:
            self._cleanup()
        else:
            self._last_esc_press = now
            self.notify("再按 Esc 退出战斗", title="提示")

    def action_basic_attack(self) -> None:
        """Q: basic attack on current cursor target."""
        if self._controller is None or self._battle_over_shown:
            return
        if not self._controller._is_seele_turn():
            self.notify("等待我方回合", title="提示")
            return
        target = self._selector.get_primary()
        if target is None:
            self.notify("无有效目标", title="提示")
            return
        snapshot = self._controller.player_basic_attack(target)
        self._refresh_from_snapshot(snapshot)
        if snapshot.is_battle_over:
            self._show_battle_over(snapshot)
        else:
            self._handle_snapshot_flow(snapshot)

    def action_skill(self) -> None:
        """E: skill on current cursor target (costs SP)."""
        if self._controller is None or self._battle_over_shown:
            return
        if not self._controller._is_seele_turn():
            self.notify("等待我方回合", title="提示")
            return
        target = self._selector.get_primary()
        if target is None:
            self.notify("无有效目标", title="提示")
            return
        snapshot = self._controller.player_skill(target)
        self._refresh_from_snapshot(snapshot)
        if snapshot.is_battle_over:
            self._show_battle_over(snapshot)
        else:
            self._handle_snapshot_flow(snapshot)

    def action_ultimate(self, index: int) -> None:
        """1-4: fire ultimate for character N (1=Seele)."""
        if self._controller is None or self._battle_over_shown:
            return
        if index != 1:
            self.notify(f"角色 {index} 未上阵", title="提示")
            return
        if not self._controller.can_ultimate():
            self.notify("能量不足", title="提示")
            return
        target = self._selector.get_primary()
        snapshot = self._controller.try_fire_ultimate(target)
        self._refresh_from_snapshot(snapshot)
        if snapshot.is_battle_over:
            self._show_battle_over(snapshot)
        else:
            self._handle_snapshot_flow(snapshot)

    def action_cursor_left(self) -> None:
        self._selector.move_cursor(-1)
        self._refresh_arrows()

    def action_cursor_right(self) -> None:
        self._selector.move_cursor(1)
        self._refresh_arrows()

    def action_show_char_status(self) -> None:
        if self._controller is None:
            return
        seele = self._controller.seele_id
        if seele:
            self._show_entity_status(seele)

    def action_show_enemy_status(self) -> None:
        if self._controller is None:
            return
        for eid in self._controller.enemy_ids:
            if self._controller._is_alive(eid):
                self._show_entity_status(eid)
                return

    # ── Private: snapshot / flow ────────────────────

    def _refresh_from_snapshot(self, snapshot: BattleSnapshot) -> None:
        """Update all widgets from a battle snapshot."""
        self.update_characters(snapshot.characters)
        self.update_enemies(snapshot.enemies)
        self.update_skill_points(
            current=snapshot.skill_point_current,
            max_sp=snapshot.skill_point_max,
        )
        self.update_turn_spinner(snapshot.is_player_turn)
        self.update_action_bar(
            snapshot.action_bar_entries,
            snapshot.current_actor_id,
        )

        for style, msg in snapshot.log_messages:
            self.query_one("#log", RichLog).write(
                Text.from_markup(f"[{style}]{msg}[/]")
            )

        # Set up selectors AFTER grid resize is applied.
        # Defer via call_after_refresh so Textual lays out the grid first.
        if snapshot.needs_input and not snapshot.is_battle_over:
            self.call_after_refresh(
                self._enable_target_selection, snapshot
            )
        else:
            self.call_after_refresh(self._clear_selectors)

    def _handle_snapshot_flow(self, snapshot: BattleSnapshot) -> None:
        """Decide what to do after a turn: wait for input or auto-advance."""
        if snapshot.is_battle_over:
            self._show_battle_over(snapshot)
            return

        if not snapshot.needs_input:
            self._schedule_enemy_turn()

    def _enable_target_selection(self, snapshot: BattleSnapshot) -> None:
        """Set up target selector for player's turn."""
        alive_targets = [t for t in snapshot.enemy_targets if t.is_alive]
        if not alive_targets:
            return

        self.setup_target_selector(
            targets=alive_targets,
            primary_id=alive_targets[0].entity_id,
            rule=SingleTargetRule(),
        )

    def _clear_selectors(self) -> None:
        """Hide both enemy and ally selector arrows."""
        self._selector.update_targets([], None)
        self._refresh_arrows()

    def _schedule_enemy_turn(self) -> None:
        """Schedule auto-advance for enemy's turn."""
        self.set_timer(_ENEMY_ADVANCE_DELAY, self._process_enemy_turn)

    def _process_enemy_turn(self) -> None:
        """Execute enemy's turn and continue the flow."""
        if self._controller is None or self._battle_over_shown:
            return

        snapshot = self._controller.advance_enemy_turn()
        self._refresh_from_snapshot(snapshot)
        self._handle_snapshot_flow(snapshot)

    def _show_battle_over(self, snapshot: BattleSnapshot) -> None:
        """Display battle over panel."""
        if self._battle_over_shown:
            return
        self._battle_over_shown = True
        self._selector.update_targets([], None)

        if snapshot.victory:
            msg = "[bold green]*** Victory! ***[/]"
        else:
            msg = "[bold red]*** Seele defeated... ***[/]"

        self.query_one("#log", RichLog).write(msg)
        self.notify(
            "双击 Esc 返回主菜单",
            title="战斗胜利" if snapshot.victory else "战斗失败",
        )

    def _show_entity_status(self, entity_id: int) -> None:
        """Show entity stats in a modal dialog."""
        import esper

        hp = esper.try_component(entity_id, HealthComponent)
        atk = esper.try_component(entity_id, AttackComponent)
        dfn = esper.try_component(entity_id, DefenseComponent)
        spd = esper.try_component(entity_id, SpeedComponent)
        en = esper.try_component(entity_id, StandardEnergyComponent)
        cr = esper.try_component(entity_id, CritRateComponent)
        cd = esper.try_component(entity_id, CritDamageComponent)
        st = esper.try_component(entity_id, CharacterStatusComponent)

        data = {}
        if hp:
            data["HP"] = f"{hp.value:.0f}/{hp.max_value:.0f}"
        if atk:
            data["ATK"] = f"{atk.value:.1f}"
        if dfn:
            data["DEF"] = f"{dfn.value:.1f}"
        if spd:
            data["SPD"] = f"{spd.final_speed:.1f}"
        if en:
            data["Energy"] = f"{en.energy:.0f}/{en.max_energy:.0f}"
        if cr:
            data["Crit Rate"] = f"{cr.value * 100:.1f}%"
        if cd:
            data["Crit DMG"] = f"{cd.value * 100:.1f}%"
        if st:
            data["Status"] = st.status.value

        if self._controller is None:
            return
        self.app.push_screen(
            StatusDialog(self._controller._entity_label(entity_id), data)
        )

    def _cleanup(self) -> None:
        if self._controller is not None:
            self._controller.cleanup()
            self._controller = None
        self.app.pop_screen()

    # ── Arrow rendering ─────────────────────────────

    def _refresh_arrows(self) -> None:
        states = self._selector.get_arrow_states()
        enemies = [s for s in states if s.is_enemy]
        allies = [s for s in states if not s.is_enemy]

        for i in range(_MAX_ENEMIES):
            w = self.query_one(f"#sel-e-{i}", Static)
            if i < len(enemies):
                w.update(_arrow_text(enemies[i]))
            else:
                w.update(Text(""))

        for i in range(_MAX_CHARS):
            w = self.query_one(f"#sel-a-{i}", Static)
            if i < len(allies):
                w.update(_arrow_text(allies[i]))
            else:
                w.update(Text(""))

    def _resize_enemy_grid(self, count: int) -> None:
        n = max(1, count)
        cols = " ".join(["1fr"] * n)
        style_spec = f"grid-size: {n}; grid-columns: {cols};"

        sel_grid = self.query_one("#selector-e")
        sel_grid.set_styles(style_spec)

        enemy_grid = self.query_one("#enemy-grid")
        enemy_grid.set_styles(style_spec)


def _arrow_text(state: ArrowState) -> Text:
    """Build a single-character Rich Text for an arrow cell."""
    if state.symbol == " " or not state.symbol:
        return Text(" ")
    return Text(
        state.symbol,
        style=Style(
            color=state.color,
            bold=state.bold,
        ),
    )
