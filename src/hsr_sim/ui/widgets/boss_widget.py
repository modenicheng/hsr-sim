from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.containers import Container, Horizontal
from textual.timer import Timer
from textual.widgets import Static

from .weakness_display import ELEMENT_COLORS, ELEMENT_SHORT

_BAR_SEGMENT = 80
_FLASH_DELAY = 0.2
_DECAY_INTERVAL = 0.04
_DECAY_STEPS = 5


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

        # ── Animation state ──
        self._anim_state: str = "idle"  # idle | flash | decay
        self._flash_type: str = "damage"  # damage | heal
        self._total_flash: int = 0
        self._decay_step: int = 0
        self._delay_timer: Timer | None = None
        self._decay_timer: Timer | None = None

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
        old_hp = self._hp
        if name is not None:
            self._name = name
        if hp is not None:
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

        if hp is not None and hp != old_hp:
            self._start_hp_animation(old_hp, hp)

        self._refresh_content()

    # ── HP animation ────────────────────────────────

    def _start_hp_animation(self, old_val: float, new_val: float) -> None:
        self._stop_animation_timers()

        max_val = max(self._max_hp, 1.0)
        old_fill = min(
            int(_BAR_SEGMENT * max(0.0, old_val) / max_val), _BAR_SEGMENT
        )
        new_fill = min(
            int(_BAR_SEGMENT * max(0.0, new_val) / max_val), _BAR_SEGMENT
        )

        delta = abs(new_fill - old_fill)
        if delta <= 0:
            self._anim_state = "idle"
            return

        self._total_flash = delta
        self._decay_step = 0

        if new_val < old_val:
            self._flash_type = "damage"
        else:
            self._flash_type = "heal"

        self._anim_state = "flash"
        self._delay_timer = self.set_timer(
            _FLASH_DELAY, self._on_delay_done
        )

    def _on_delay_done(self) -> None:
        self._anim_state = "decay"
        self._decay_timer = self.set_interval(
            _DECAY_INTERVAL, self._on_decay_tick
        )

    def _on_decay_tick(self) -> None:
        self._decay_step += 1
        self._refresh_hp_line()
        if self._decay_step >= _DECAY_STEPS:
            self._anim_state = "idle"
            if self._decay_timer:
                self._decay_timer.stop()
                self._decay_timer = None

    def _stop_animation_timers(self) -> None:
        if self._delay_timer is not None:
            self._delay_timer.stop()
            self._delay_timer = None
        if self._decay_timer is not None:
            self._decay_timer.stop()
            self._decay_timer = None

    # ── Content refresh ─────────────────────────────

    def _refresh_content(self) -> None:
        # Line 1: name + toughness + weakness
        name = Text(f"[{self._name}]", style=Style(bold=True, color="red"))
        self.query_one("#boss-name", Static).update(name)

        if self._max_toughness > 0:
            tough_text = _build_bar(
                self._toughness,
                self._max_toughness,
                filled_color=(
                    "grey42" if self._toughness_locked else "white"
                ),
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
                f"[{n} x{s}]" if s > 1 else f"[{n}]" for n, s in self._buffs
            ]
            buffs_text.append(" ".join(parts), style=Style(color="#87CEEB"))
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

        if self._anim_state == "idle":
            hp_text = _build_bar(
                safe_val,
                max_val,
                filled_color="red",
                empty_color="grey42",
                fill_char="=",
                empty_char="-",
                segment=_BAR_SEGMENT,
            )
        elif self._anim_state == "flash":
            hp_text = _build_anim_bar(
                safe_val, max_val, progress=0.0,
                flash_type=self._flash_type,
                total_flash=self._total_flash,
            )
        else:  # decay
            progress = min(1.0, self._decay_step / _DECAY_STEPS)
            hp_text = _build_anim_bar(
                safe_val, max_val, progress=progress,
                flash_type=self._flash_type,
                total_flash=self._total_flash,
            )

        self.query_one("#boss-hp", Static).update(hp_text)

        pct = safe_val / max_val * 100
        pct_text = Text(f"[{pct:.0f}%]", style=Style(color="white"))
        self.query_one("#boss-hp-pct", Static).update(pct_text)


# ── Helper functions ───────────────────────────────────

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


def _build_anim_bar(
    current: float,
    max_value: float,
    progress: float,
    flash_type: str,
    total_flash: int,
) -> Text:
    """Build animated HP bar with flash overlay.

    progress: 0.0 (full flash) to 1.0 (no flash).
    """
    cur_fill = min(
        int(_BAR_SEGMENT * current / max_value), _BAR_SEGMENT
    )
    flash_visible = int(total_flash * (1.0 - progress))

    result = Text()

    if flash_type == "damage":
        colored = cur_fill
        empty = _BAR_SEGMENT - colored - flash_visible
        result.append("=" * max(0, colored), style=Style(color="red"))
        result.append(
            "=" * max(0, flash_visible), style=Style(color="white")
        )
        result.append("-" * max(0, empty), style=Style(color="grey42"))
    else:  # heal
        base = cur_fill - total_flash
        filled = int(total_flash * progress)
        colored = max(0, base) + filled
        empty = _BAR_SEGMENT - colored - flash_visible
        result.append("=" * max(0, colored), style=Style(color="red"))
        result.append(
            "=" * max(0, flash_visible), style=Style(color="green")
        )
        result.append("-" * max(0, empty), style=Style(color="grey42"))

    return result


def _build_weakness(types: list[str], disabled: bool = False) -> Text:
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
