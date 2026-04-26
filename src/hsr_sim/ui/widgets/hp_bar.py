from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget


class HpBarWidget(Widget):
    """Two-layer HP bar.

    Current HP (colored) + shield (white) + consumed (dim).
    Upper layer: current HP; Lower layer: shield amount.
    """

    DEFAULT_CSS = """
    HpBarWidget {
        height: 2;
        width: 100%;
    }
    """

    def __init__(
        self,
        value: float = 0.0,
        max_value: float = 100.0,
        shield: float = 0.0,
        color: str = "cyan",
        show_percent: bool = True,
        bar_width: int = 0,
        prefix: str = "",
        shield_indent: int = 0,
        name: str = "",
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.value = value
        self.max_value = max_value
        self.shield = shield
        self.color = color
        self.show_percent = show_percent
        self.bar_width = bar_width
        self.prefix = prefix
        self.shield_indent = shield_indent
        self._prev_value = value
        self._buffer_frames = 0

    def update_hp(
        self,
        value: float,
        max_value: float | None = None,
        shield: float | None = None,
    ) -> None:
        if max_value is not None:
            self.max_value = max_value
        if shield is not None:
            self.shield = shield
        if value < self.value:
            self._buffer_frames = 3
            self._prev_value = self.value
        self.value = value
        self.refresh()

    def render(self) -> Text:
        max_val = max(self.max_value, 1.0)
        safe_val = max(0.0, self.value)
        safe_shield = max(0.0, self.shield)

        # Dynamic total width from widget, fallback to bar_width/default.
        total_w = self.size.width
        if total_w <= 0:
            total_w = self.bar_width if self.bar_width > 0 else 20

        pct_text = ""
        if self.show_percent:
            pct = safe_val / max_val * 100
            pct_text = f"[{pct:.0f}%]"
        pct_suffix = f" {pct_text}" if pct_text else ""

        # Reserve width for prefix and optional pct suffix.
        max_w = total_w - len(self.prefix) - len(pct_suffix)
        max_w = max(1, max_w)

        # Upper line: prefix + HP bar
        hp_fill = min(int(max_w * safe_val / max_val), max_w)
        hp_empty = max_w - hp_fill

        hp_line = Text()
        if self.prefix:
            hp_line.append(self.prefix, style=Style(color="white"))
        hp_line.append("=" * hp_fill, style=Style(color=self.color))
        hp_line.append("-" * hp_empty, style=Style(color="grey42"))

        # Lower line: indent + shield bar
        shield_width = min(int(max_w * safe_shield / max_val), max_w)
        shield_line = Text()
        if self.shield_indent > 0:
            shield_line.append(" " * self.shield_indent)
        shield_line.append(
            "=" * shield_width, style=Style(color="white")
        )

        # Buffer effect: flash white for damage taken
        if self._buffer_frames > 0 and self._prev_value > self.value:
            lost = int(
                max_w
                * min(self._prev_value - self.value, max_val)
                / max_val
            )
            flash_start = max(0, hp_fill)
            flash_end = min(flash_start + lost, max_w)
            flash_width = flash_end - flash_start
            if flash_width > 0:
                new_hp = Text()
                new_hp.append(
                    "=" * flash_start, style=Style(color=self.color)
                )
                new_hp.append(
                    "=" * flash_width, style=Style(color="white")
                )
                rem = max_w - flash_end
                if rem > 0:
                    new_hp.append(
                        "-" * rem, style=Style(color="grey42")
                    )
                hp_line = Text()
                if self.prefix:
                    hp_line.append(
                        self.prefix, style=Style(color="white")
                    )
                hp_line.append_text(new_hp)
            self._buffer_frames -= 1

        result = Text()
        result.append(hp_line)
        if pct_suffix:
            result.append(pct_suffix, style=Style(color="white"))
        result.append("\n")
        result.append(shield_line)
        return result
