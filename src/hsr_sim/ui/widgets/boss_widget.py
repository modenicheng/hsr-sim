from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.containers import Container, Horizontal
from textual.widgets import Static

from .weakness_display import ELEMENT_COLORS, ELEMENT_SHORT

_BAR_SEGMENT = 80


class BossWidget(Container):
    """Boss section: name+toughness+weakness, HP bar, buffs+stacks.

    Design:
        [BOSS_NAME]=======================================[弱点]
        ============================-----------------------[50%]
        [buff]                                         [特殊叠层]
    """

    DEFAULT_CSS = """
    BossWidget {
        width: 75%;
        height: auto;
        margin: 0 2;
    }

    BossWidget Horizontal {
        width: 100%;
        height: 1;
    }

    #boss-name {
        text-style: bold;
        width: auto;
    }

    #boss-toughness {
        width: 1fr;
        overflow: hidden;
    }

    #boss-weakness {
        width: auto;
    }

    #boss-hp {
        width: 1fr;
        overflow: hidden;
    }

    #boss-hp-pct {
        width: auto;
    }

    #boss-buffs {
        width: 1fr;
    }

    #boss-special {
        width: auto;
    }
    """

    def __init__(
        self,
        name: str = "",
        hp: float = 0.0,
        max_hp: float = 100.0,
        toughness: int = 0,
        max_toughness: int = 0,
        toughness_locked: bool = False,
        weakness_types: list[str] | None = None,
        weakness_disabled: bool = False,
        buffs: list[tuple[str, int]] | None = None,
        special_stacks: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._name = name
        self._hp = hp
        self._max_hp = max_hp
        self._toughness = toughness
        self._max_toughness = max_toughness
        self._toughness_locked = toughness_locked
        self._weakness_types = weakness_types or []
        self._weakness_disabled = weakness_disabled
        self._buffs = buffs or []
        self._special_stacks = special_stacks
        self._prev_hp = hp
        self._buffer_frames = 0

    def compose(self):
        with Horizontal(id="boss-info"):
            yield Static("", id="boss-name")
            yield Static("", id="boss-toughness")
            yield Static("", id="boss-weakness")
        with Horizontal(id="boss-hp-row"):
            yield Static("", id="boss-hp")
            yield Static("", id="boss-hp-pct")
        with Horizontal(id="boss-buffs-row"):
            yield Static("", id="boss-buffs")
            yield Static("", id="boss-special")

    def on_mount(self) -> None:
        self._refresh_content()

    def update_state(
        self,
        name: str | None = None,
        hp: float | None = None,
        max_hp: float | None = None,
        toughness: int | None = None,
        max_toughness: int | None = None,
        toughness_locked: bool | None = None,
        weakness_types: list[str] | None = None,
        weakness_disabled: bool | None = None,
        buffs: list[tuple[str, int]] | None = None,
        special_stacks: str | None = None,
    ) -> None:
        if name is not None:
            self._name = name
        if hp is not None:
            if hp < self._hp:
                self._buffer_frames = 3
                self._prev_hp = self._hp
            self._hp = hp
        if max_hp is not None:
            self._max_hp = max_hp
        if toughness is not None:
            self._toughness = toughness
        if max_toughness is not None:
            self._max_toughness = max_toughness
        if toughness_locked is not None:
            self._toughness_locked = toughness_locked
        if weakness_types is not None:
            self._weakness_types = weakness_types
        if weakness_disabled is not None:
            self._weakness_disabled = weakness_disabled
        if buffs is not None:
            self._buffs = buffs
        if special_stacks is not None:
            self._special_stacks = special_stacks
        self._refresh_content()

    def _refresh_content(self) -> None:
        # Line 1: name + toughness + weakness
        name = Text(f"[{self._name}]", style=Style(bold=True, color="red"))
        self.query_one("#boss-name", Static).update(name)

        if self._max_toughness > 0:
            tough_text = _build_bar(
                self._toughness,
                self._max_toughness,
                filled_color="grey42"
                if self._toughness_locked
                else "white",
                empty_color="grey42",
                fill_char="=",
                empty_char="-",
                segment=_BAR_SEGMENT,
            )
        else:
            tough_text = Text(
                "=" * _BAR_SEGMENT, style=Style(color="grey42")
            )
        self.query_one("#boss-toughness", Static).update(tough_text)

        weakness = _build_weakness(
            self._weakness_types, self._weakness_disabled
        )
        self.query_one("#boss-weakness", Static).update(weakness)

        # Line 2: HP bar + percentage
        self._refresh_hp_line()

        # Line 3: buffs + special stacks
        buffs_text = Text()
        if self._buffs:
            parts = [
                f"[{n} x{s}]" if s > 1 else f"[{n}]"
                for n, s in self._buffs
            ]
            buffs_text.append(
                " ".join(parts), style=Style(color="#87CEEB")
            )
        self.query_one("#boss-buffs", Static).update(buffs_text)

        special = Text()
        if self._special_stacks:
            special.append(
                self._special_stacks, style=Style(color="yellow")
            )
        self.query_one("#boss-special", Static).update(special)

    def _refresh_hp_line(self) -> None:
        safe_val = max(0.0, self._hp)
        max_val = max(self._max_hp, 1.0)
        if self._buffer_frames > 0 and self._prev_hp > self._hp:
            prev_safe = min(self._prev_hp, max_val)
            hp_text = _build_damage_flash_bar(
                safe_val, prev_safe, max_val, _BAR_SEGMENT
            )
            self._buffer_frames -= 1
            self.set_timer(0.1, self._refresh_hp_line)
        else:
            hp_text = _build_bar(
                safe_val,
                max_val,
                filled_color="red",
                empty_color="grey42",
                fill_char="=",
                empty_char="-",
                segment=_BAR_SEGMENT,
            )
        self.query_one("#boss-hp", Static).update(hp_text)

        pct = safe_val / max_val * 100
        pct_text = Text(f"[{pct:.0f}%]", style=Style(color="white"))
        self.query_one("#boss-hp-pct", Static).update(pct_text)


def _build_bar(
    value: float,
    max_value: float,
    filled_color: str,
    empty_color: str,
    fill_char: str = "=",
    empty_char: str = "-",
    segment: int = _BAR_SEGMENT,
) -> Text:
    fill = min(int(segment * value / max_value), segment)
    empty = segment - fill
    result = Text()
    result.append(fill_char * fill, style=Style(color=filled_color))
    result.append(empty_char * empty, style=Style(color=empty_color))
    return result


def _build_damage_flash_bar(
    current: float,
    previous: float,
    max_value: float,
    segment: int = _BAR_SEGMENT,
) -> Text:
    cur_fill = min(int(segment * current / max_value), segment)
    lost = min(int(segment * (previous - current) / max_value), segment)
    flash = min(lost, segment - cur_fill)
    remaining = segment - cur_fill - flash
    result = Text()
    result.append("=" * cur_fill, style=Style(color="red"))
    result.append("=" * flash, style=Style(color="white"))
    result.append("-" * remaining, style=Style(color="grey42"))
    return result


def _build_weakness(
    types: list[str], disabled: bool = False
) -> Text:
    result = Text()
    if not types:
        return result
    result.append("[", style=Style(color="white"))
    for w in types:
        short = ELEMENT_SHORT.get(w, w[:1])
        elem_style = (
            Style(color="grey42")
            if disabled
            else Style(color=ELEMENT_COLORS.get(w, "#FFF"), bold=True)
        )
        result.append(short, style=elem_style)
    result.append("]", style=Style(color="white"))
    return result
