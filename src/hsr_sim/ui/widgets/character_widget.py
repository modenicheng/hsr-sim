from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.containers import Container, Horizontal
from textual.widgets import Static

from .hp_bar import HpBarWidget


class CharacterWidget(Container):
    """A single character card: name, stacks+energy, HP bar, shield, buffs.

    Design:
        角色1
        [技能叠层]       [能量/max]¹
        HP============--------------
          ===============
        [buff]
    """

    DEFAULT_CSS = """
    CharacterWidget {
        width: 20;
        height: auto;
        padding: 0 1;
    }

    CharacterWidget.dead {
        opacity: 50%;
    }

    CharacterWidget .char-name {
        text-style: bold;
        height: 1;
    }

    CharacterWidget HpBarWidget {
        height: 2;
        width: 100%;
    }

    CharacterWidget .stats-left {
        width: 1fr;
    }

    CharacterWidget .stats-right {
        width: auto;
        content-align: right middle;
    }

    CharacterWidget .bottom-left {
        width: 1fr;
    }

    CharacterWidget .bottom-right {
        width: auto;
        content-align: right middle;
    }
    """

    def __init__(
        self,
        name: str = "",
        hp: float = 0.0,
        max_hp: float = 100.0,
        shield: float = 0.0,
        energy: float = 0.0,
        max_energy: float = 120.0,
        stacks: list[tuple[str, int, int]] | None = None,
        buffs: list[tuple[str, int]] | None = None,
        energy_key: int = 0,
        is_current_actor: bool = False,
        is_alive: bool = True,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.char_name = name
        self._hp = hp
        self._max_hp = max_hp
        self._shield = shield
        self._energy = energy
        self._max_energy = max_energy
        self._stacks = stacks or []
        self._buffs = buffs or []
        self._energy_key = energy_key
        self._is_current_actor = is_current_actor
        self._is_alive = is_alive

    def compose(self):
        yield Static("", classes="char-name")

        yield Horizontal(
            Static("", classes="stats-left"),
            Static("", classes="stats-right"),
            classes="char-stats",
        )

        yield HpBarWidget(
            value=self._hp,
            max_value=self._max_hp,
            shield=self._shield,
            color="cyan",
            show_percent=False,
            bar_width=18,
            prefix="HP",
            shield_indent=2,
        )

        yield Horizontal(
            Static("", classes="bottom-left"),
            Static("", classes="bottom-right"),
            classes="char-bottom",
        )

    def on_mount(self) -> None:
        self._refresh_classes()
        self._refresh_content()

    def update_state(
        self,
        name: str | None = None,
        hp: float | None = None,
        max_hp: float | None = None,
        shield: float | None = None,
        energy: float | None = None,
        max_energy: float | None = None,
        stacks: list[tuple[str, int, int]] | None = None,
        buffs: list[tuple[str, int]] | None = None,
        energy_key: int | None = None,
        is_current_actor: bool | None = None,
        is_alive: bool | None = None,
    ) -> None:
        if name is not None:
            self.char_name = name
        if hp is not None:
            self._hp = hp
        if max_hp is not None:
            self._max_hp = max_hp
        if shield is not None:
            self._shield = shield
        if energy is not None:
            self._energy = energy
        if max_energy is not None:
            self._max_energy = max_energy
        if stacks is not None:
            self._stacks = stacks
        if buffs is not None:
            self._buffs = buffs
        if energy_key is not None:
            self._energy_key = energy_key
        if is_current_actor is not None:
            self._is_current_actor = is_current_actor
        if is_alive is not None:
            self._is_alive = is_alive

        hp_bar = self.query_one(HpBarWidget)
        hp_bar.update_hp(self._hp, self._max_hp, self._shield)

        self._refresh_classes()
        self._refresh_content()

    def _refresh_classes(self) -> None:
        if not self._is_alive:
            self.add_class("dead")
        else:
            self.remove_class("dead")
        if self._is_current_actor:
            self.add_class("current-actor")
        else:
            self.remove_class("current-actor")

    def _refresh_content(self) -> None:
        name_w = self.query_one(".char-name", Static)
        name_text = Text()
        name_text.append(
            self.char_name,
            style=Style(bold=True, reverse=self._is_current_actor),
        )
        name_w.update(name_text)

        # Line 2: stacks left, energy right (width: 1fr pushes right)
        left_w = self.query_one(".stats-left", Static)
        left_text = Text()
        if self._stacks:
            s_text = " ".join(f"[{stype}:{current}/{max_s}]"
                              for stype, current, max_s in self._stacks)
            left_text.append(s_text, style=Style(color="yellow"))
        left_w.update(left_text)

        ENERGY_KEY_MAP = {1: "¹", 2: "²", 3: "³", 4: "⁴"}

        right_w = self.query_one(".stats-right", Static)
        key_hint = ENERGY_KEY_MAP.get(
            self._energy_key) if 1 <= self._energy_key <= 4 else ""
        right_text = Text()
        right_text.append(
            f"[{self._energy:.0f}/{self._max_energy:.0f}]",
            style=Style(color="magenta"),
        )
        if key_hint:
            right_text.append(key_hint, style=Style(color="grey62"))
        right_w.update(right_text)

        # Line 5: buffs left, hp/max right (width: 1fr pushes right)
        bottom_left = self.query_one(".bottom-left", Static)
        bottom_left_text = Text()
        if self._buffs:
            parts = []
            for bname, bstacks in self._buffs:
                if bstacks > 1:
                    parts.append(f"[{bname} x{bstacks}]")
                else:
                    parts.append(f"[{bname}]")
            bottom_left_text.append(" ".join(parts),
                                    style=Style(color="#87CEEB"))
        bottom_left.update(bottom_left_text)

        bottom_right = self.query_one(".bottom-right", Static)
        bottom_right_text = Text(
            f"[{self._hp:.0f}/{self._max_hp:.0f}]",
            style=Style(color="white"),
        )
        bottom_right.update(bottom_right_text)
