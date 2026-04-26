"""BattleScreen — main TUI battle view composing all battle widgets."""

from __future__ import annotations

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Container, Grid, Horizontal
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Static

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


class BattleScreen(Screen):
    """Main battle screen.

    Layout:
        #boss-section     (auto, hidden by default) — BOSS HP area
        #body             (1fr, grid: 22 | 1fr)
          #action-column  (22) — action bar + status buttons below
          #main-area      (1fr) — top enemy-parent / middle selectors /
                                bottom ally-parent
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
        height: 2;
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
    """

    BINDINGS = [
        ("escape", "quit_battle", "退出战斗"),
        ("q", "quit_battle", "退出"),
        ("c", "show_char_status", "角色状态"),
        ("e", "show_enemy_status", "敌方状态"),
        ("left", "cursor_left", "←"),
        ("right", "cursor_right", "→"),
        ("1", "select_target(1)", "目标1"),
        ("2", "select_target(2)", "目标2"),
        ("3", "select_target(3)", "目标3"),
        ("4", "select_target(4)", "目标4"),
        ("5", "select_target(5)", "目标5"),
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
                                yield CharacterWidget(
                                    id=f"char-{i}"
                                )
                        with Container(id="sp-column"):
                            yield SkillPointWidget(id="sp-widget")
                            yield TurnSpinnerWidget(
                                id="turn-spinner", is_player_turn=True
                            )

    def on_mount(self) -> None:
        self._selector = TargetSelector()

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

        self._setup_demo_state()
        self._refresh_arrows()

    # ── Public update API ───────────────────────────

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
        """Update enemy widgets from list of dicts."""
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
        self._refresh_arrows()

    def update_characters(self, characters: list[dict]) -> None:
        for i in range(1, _MAX_CHARS + 1):
            w = self.query_one(f"#char-{i}", CharacterWidget)
            if i <= len(characters):
                data = characters[i - 1]
                w.update_state(
                    name=data.get("name", f"角色{i}"),
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
        """Update skill point display.

        Args:
            current: Current skill points (0..max_sp).
            max_sp: Maximum skill points (0..12).
        """
        w = self.query_one("#sp-widget", SkillPointWidget)
        w.update_sp(current=current, max_sp=max_sp)

    def update_turn_spinner(self, is_player_turn: bool) -> None:
        """Set turn spinner active (player turn) or dimmed (enemy turn).

        Args:
            is_player_turn: True to show animated spinner, False to dim.
        """
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

    def get_selector(self) -> TargetSelector:
        return self._selector

    # ── Actions / Bindings ──────────────────────────

    def action_quit_battle(self) -> None:
        self.post_message(self.QuitBattle())

    def action_cursor_left(self) -> None:
        self._selector.move_cursor(-1)
        self._refresh_arrows()

    def action_cursor_right(self) -> None:
        self._selector.move_cursor(1)
        self._refresh_arrows()

    def action_show_char_status(self) -> None:
        data = {"角色状态": "开发中", "按 c 键或点击按钮查看详情": ""}
        self.app.push_screen(StatusDialog("角色详情", data))

    def action_show_enemy_status(self) -> None:
        data = {"敌方状态": "开发中", "按 e 键或点击按钮查看详情": ""}
        self.app.push_screen(StatusDialog("敌方详情", data))

    def action_select_target(self, index: int) -> None:
        targets = self._selector.targets
        idx = index - 1
        if 0 <= idx < len(targets):
            self.post_message(
                self.TargetSelected(targets[idx].entity_id)
            )

    def on_compact_button_pressed(
        self, event: CompactButton.Pressed
    ) -> None:
        bid = event.button.id or ""
        if bid == "btn-char-status":
            self.action_show_char_status()
        elif bid == "btn-enemy-status":
            self.action_show_enemy_status()

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
                ally = allies[i]
                if ally.symbol:
                    w.update(_arrow_text(ally))
                else:
                    w.update(
                        Text("▽", style=Style(color="grey50"))
                    )
            else:
                w.update(Text("▽", style=Style(color="grey50")))

    def _resize_enemy_grid(self, count: int) -> None:
        """Update grid-size and grid-columns for #enemy-grid and #selector-e."""
        n = max(1, count)
        cols = " ".join(["1fr"] * n)
        style_spec = f"grid-size: {n}; grid-columns: {cols};"

        sel_grid = self.query_one("#selector-e")
        sel_grid.set_styles(style_spec)

        enemy_grid = self.query_one("#enemy-grid")
        enemy_grid.set_styles(style_spec)

    # ── Demo ────────────────────────────────────────

    def _setup_demo_state(self) -> None:
        self.update_boss(
            name="BOSS",
            hp=80000,
            max_hp=100000,
            toughness=60,
            max_toughness=80,
            toughness_locked=False,
            weakness_types=["fire", "physical", "imaginary"],
            weakness_disabled=False,
            buffs=[("攻击强化", 2)],
            special_stacks="[复仇 3/5]",
        )
        self.update_enemies(
            [
                {
                    "name": "Enemy1",
                    "hp": 30000,
                    "max_hp": 40000,
                    "toughness": 3,
                    "max_toughness": 5,
                    "toughness_locked": False,
                    "weakness_types": ["physical"],
                    "weakness_disabled": False,
                },
                {
                    "name": "Enemy2",
                    "hp": 15000,
                    "max_hp": 40000,
                    "toughness": 1,
                    "max_toughness": 4,
                    "toughness_locked": False,
                    "weakness_types": ["fire", "ice"],
                    "weakness_disabled": False,
                },
                {
                    "name": "Enemy3",
                    "hp": 40000,
                    "max_hp": 40000,
                    "toughness": 5,
                    "max_toughness": 5,
                    "toughness_locked": True,
                    "weakness_types": ["lightning"],
                    "weakness_disabled": True,
                },
                {
                    "name": "Enemy4",
                    "hp": 8000,
                    "max_hp": 40000,
                    "toughness": 0,
                    "max_toughness": 4,
                    "toughness_locked": False,
                    "weakness_types": ["wind", "quantum"],
                    "weakness_disabled": False,
                },
                {
                    "name": "Enemy5",
                    "hp": 20000,
                    "max_hp": 40000,
                    "toughness": 2,
                    "max_toughness": 3,
                    "toughness_locked": False,
                    "weakness_types": ["imaginary"],
                    "weakness_disabled": False,
                },
            ]
        )
        self.update_characters(
            [
                {
                    "name": "Seele",
                    "hp": 8500,
                    "max_hp": 10000,
                    "shield": 2000,
                    "energy": 95,
                    "max_energy": 120,
                    "stacks": [("seele_spd", 1, 2)],
                    "buffs": [("SPD+", 1)],
                    "is_current_actor": True,
                    "is_alive": True,
                },
                {
                    "name": "Bronya",
                    "hp": 12000,
                    "max_hp": 15000,
                    "shield": 0,
                    "energy": 60,
                    "max_energy": 120,
                    "stacks": [],
                    "buffs": [],
                    "is_current_actor": False,
                    "is_alive": True,
                },
                {
                    "name": "Tingyun",
                    "hp": 3000,
                    "max_hp": 8000,
                    "shield": 5000,
                    "energy": 110,
                    "max_energy": 130,
                    "stacks": [],
                    "buffs": [("ATK+", 1)],
                    "is_current_actor": False,
                    "is_alive": True,
                },
                {
                    "name": "Luocha",
                    "hp": 0,
                    "max_hp": 12000,
                    "shield": 0,
                    "energy": 0,
                    "max_energy": 100,
                    "stacks": [],
                    "buffs": [],
                    "is_current_actor": False,
                    "is_alive": False,
                },
            ]
        )
        self.update_skill_points(current=3, max_sp=5)
        self.update_action_bar(
            entries=[
                (101, "Enemy1", 75.0, 133.0, True),
                (102, "Seele", 78.0, 149.0, False),
                (103, "Enemy2", 80.0, 125.0, True),
                (104, "Bronya", 90.0, 140.0, False),
                (105, "Enemy3", 95.0, 105.0, True),
                (106, "Tingyun", 100.0, 112.0, False),
                (107, "Enemy4", 105.0, 95.0, True),
                (108, "Enemy5", 110.0, 91.0, True),
            ],
            current_actor=102,
        )

        enemy_targets = [
            TargetInfo(
                entity_id=201 + i, label=f"Enemy{i + 1}", is_enemy=True
            )
            for i in range(5)
        ]
        char_targets = [
            TargetInfo(
                entity_id=301 + i, label=f"Char{i + 1}", is_enemy=False
            )
            for i in range(4)
        ]
        self.setup_target_selector(
            targets=enemy_targets + char_targets,
            primary_id=201,
            rule=SingleTargetRule(),
        )


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
