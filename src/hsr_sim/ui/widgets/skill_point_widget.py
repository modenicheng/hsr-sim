from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget

FILLED = "♦"
EMPTY = "♢"
PER_LINE = 5


class SkillPointWidget(Widget):
    """Skill Point (战技点) display.

    Shows filled (♦) and empty (♢) diamonds. Max 5 per line.
    When max > 5, overflow slots render on a line above the main row.

    Design:
        ♦♦♦♢♢           (max ≤ 5)
        [3/5]

        ♢♢               (max = 7)
        ♦♦♦♢♢
        [3/7]

        ♢♢♢♢♢♢♢        (max = 12)
          ♦♦♦♢♢
         [3/12]
    """

    DEFAULT_CSS = """
    SkillPointWidget {
        width: 10;
        height: auto;
    }
    """

    def __init__(
        self,
        current: int = 3,
        max_sp: int = 5,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._current = max(0, current)
        self._max_sp = max(0, max_sp)

    # ── Public API ───────────────────────────────────

    def update_sp(
        self,
        current: int | None = None,
        max_sp: int | None = None,
    ) -> None:
        """Update skill point state. Pass None to keep current value.

        Args:
            current: Current skill points (0..max_sp).
            max_sp: Maximum skill points (0..12, default 5).
        """
        if current is not None:
            self._current = max(0, min(current, self._max_sp))
        if max_sp is not None:
            self._max_sp = max(0, max_sp)
            self._current = min(self._current, self._max_sp)
        self.refresh()

    @property
    def current(self) -> int:
        return self._current

    @property
    def max_sp(self) -> int:
        return self._max_sp

    # ── Rendering ────────────────────────────────────

    def render(self) -> Text:
        result = Text()
        total = self._max_sp
        current = min(self._current, total)
        has_overflow = total > PER_LINE

        # Overflow line (slots 6+)
        if has_overflow:
            overflow_count = total - PER_LINE
            for i in range(overflow_count):
                slot_idx = PER_LINE + i
                symbol = (
                    FILLED if slot_idx < current else EMPTY
                )
                result.append(
                    symbol,
                    style=(
                        Style(color="white", bold=True)
                        if symbol == FILLED
                        else Style(color="grey42")
                    ),
                )
            result.append("\n")

        # Main line (slots 1-5, or 1-total when ≤ 5)
        main_count = min(total, PER_LINE)
        if has_overflow:
            result.append("  ")
        for i in range(main_count):
            symbol = FILLED if i < current else EMPTY
            result.append(
                symbol,
                style=(
                    Style(color="white", bold=True)
                    if symbol == FILLED
                    else Style(color="grey42")
                ),
            )
        result.append("\n")

        # Counter line
        prefix = " " if has_overflow else ""
        result.append(
            f"{prefix}[{current}/{total}]",
            style=Style(color="white"),
        )

        return result
