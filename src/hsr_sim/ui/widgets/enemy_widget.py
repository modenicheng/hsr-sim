from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.containers import Container, Horizontal
from textual.widgets import Static

from .weakness_display import ELEMENT_COLORS, ELEMENT_SHORT


class EnemyWidget(Container):
    """Single enemy: name + weakness, toughness bar, HP bar, buffs/stacks.

    Layout (CSS-driven):
        [name]  [弱点]
        ========-------
        ========------- [XX%]
        [buffs]      [special]
    """

    DEFAULT_CSS = """
    EnemyWidget {
        width: 100%;
        height: auto;
        padding: 0 2;
    }

    EnemyWidget > .enemy-header {
        width: 100%;
        height: auto;
    }

    EnemyWidget > .enemy-header > .enemy-name {
        width: 1fr;
    }

    EnemyWidget > .enemy-header > .enemy-weakness {
        width: auto;
        max-width: 8;
        text-wrap: wrap;
        content-align: right middle;
    }

    EnemyWidget > .enemy-toughness {
        width: 100%;
        height: 1;
    }

    EnemyWidget > .enemy-hp-row {
        width: 100%;
        height: 1;
    }

    EnemyWidget > .enemy-hp-row > .enemy-hp-bar {
        width: 1fr;
    }

    EnemyWidget > .enemy-hp-row > .enemy-hp-pct {
        width: auto;
        content-align: right middle;
    }

    EnemyWidget > .enemy-bottom {
        width: 100%;
        height: auto;
    }

    EnemyWidget > .enemy-bottom > .bottom-left {
        width: 1fr;
    }

    EnemyWidget > .enemy-bottom > .bottom-right {
        width: auto;
        content-align: right middle;
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
        bar_width: int = 20,
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
        self._bar_width = bar_width
        self._prev_hp = hp
        self._buffer_frames = 0

    def compose(self):
        yield Horizontal(
            Static("", classes="enemy-name"),
            Static("", classes="enemy-weakness"),
            classes="enemy-header",
        )
        yield Static("", classes="enemy-toughness")
        yield Horizontal(
            Static("", classes="enemy-hp-bar"),
            Static("", classes="enemy-hp-pct"),
            classes="enemy-hp-row",
        )
        yield Horizontal(
            Static("", classes="bottom-left"),
            Static("", classes="bottom-right"),
            classes="enemy-bottom",
        )

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

    # ── Content refresh ───────────────────────────────

    def _refresh_content(self) -> None:
        total_w = self.size.width if self.size.width > 0 else self._bar_width + 4
        total_w = max(10, total_w)

        # Line 0: name + weakness (CSS right-aligns the weakness)
        name_text = Text()
        name_text.append(
            f"[{self._name}]", style=Style(bold=True, color="red")
        )
        self.query_one(".enemy-name", Static).update(name_text)
        self.query_one(".enemy-weakness", Static).update(
            self._build_weakness_text()
        )

        # Line 1: toughness bar
        self.query_one(".enemy-toughness", Static).update(
            self._build_toughness_text(total_w)
        )

        # Line 2: HP bar + percentage
        bar_text, pct_text = self._build_hp_texts(total_w)
        self.query_one(".enemy-hp-bar", Static).update(bar_text)
        self.query_one(".enemy-hp-pct", Static).update(pct_text)

        # Bottom row: buffs + special stacks
        self._refresh_bottom(total_w)

    # ── Weakness ─────────────────────────────────────

    def _build_weakness_text(self) -> Text:
        """Build colored weakness element symbols (no brackets)."""
        text = Text()
        if not self._weakness_types:
            return text
        for i, w in enumerate(self._weakness_types):
            short = ELEMENT_SHORT.get(w, w[:1])
            if self._weakness_disabled:
                text.append(short, style=Style(color="grey42"))
            else:
                text.append(
                    short,
                    style=Style(
                        color=ELEMENT_COLORS.get(w, "#FFF"), bold=True
                    ),
                )
        return text

    # ── Toughness bar ────────────────────────────────

    def _build_toughness_text(self, total_w: int) -> Text:
        result = Text()
        if self._max_toughness > 0:
            t_fill = min(
                int(total_w * self._toughness / self._max_toughness),
                total_w,
            )
            t_empty = total_w - t_fill
            tough_color = (
                "grey42" if self._toughness_locked else "white"
            )
            result.append("=" * t_fill, style=Style(color=tough_color))
            result.append("-" * t_empty, style=Style(color="grey42"))
        else:
            result.append("=" * total_w, style=Style(color="grey42"))
        return result

    # ── HP bar ───────────────────────────────────────

    def _build_hp_texts(self, total_w: int) -> tuple[Text, Text]:
        """Return (bar_text, pct_text) for the HP row."""
        max_val = max(self._max_hp, 1.0)
        safe_val = max(0.0, self._hp)
        # Reserve ~6 cells for "[100%]" percentage suffix
        bar_w = max(4, total_w - 7)

        hp_fill = min(int(bar_w * safe_val / max_val), bar_w)
        hp_empty = bar_w - hp_fill

        bar_text = Text()
        if self._buffer_frames > 0 and self._prev_hp > self._hp:
            lost = int(
                bar_w
                * min(self._prev_hp - self._hp, max_val)
                / max_val
            )
            flash_width = min(max(0, lost), bar_w - hp_fill)
            bar_text.append(
                "=" * hp_fill, style=Style(color="red")
            )
            bar_text.append(
                "=" * flash_width, style=Style(color="white")
            )
            bar_text.append(
                "-" * (bar_w - hp_fill - flash_width),
                style=Style(color="grey42"),
            )
            self._buffer_frames -= 1
        else:
            bar_text.append(
                "=" * hp_fill, style=Style(color="red")
            )
            bar_text.append(
                "-" * hp_empty, style=Style(color="grey42")
            )

        pct = safe_val / max_val * 100
        pct_text = Text(
            f"[{pct:.0f}%]", style=Style(color="white")
        )

        return bar_text, pct_text

    # ── Bottom row (buffs / special stacks) ──────────

    def _refresh_bottom(self, total_w: int) -> None:
        left_info = Text()
        right_info = Text()

        if self._buffs:
            buff_text = " ".join(
                f"[{n} x{s}]" if s > 1 else f"[{n}]"
                for n, s in self._buffs
            )
            left_info.append(buff_text, style=Style(color="#87CEEB"))

        if self._special_stacks:
            right_info.append(
                self._special_stacks, style=Style(color="yellow")
            )

        self.query_one(".bottom-left", Static).update(left_info)
        self.query_one(".bottom-right", Static).update(right_info)
