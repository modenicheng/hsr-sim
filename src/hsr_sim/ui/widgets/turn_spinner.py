from __future__ import annotations

from rich.style import Style
from rich.text import Text
from textual.widget import Widget

_SPIN_CHARS = ["◢", "◣", "◤", "◥"]
# _SPIN_CHARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]  # Alternative: smoother bar spinner
_SPIN_CHARS = ["⣾", "⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽",
               "⣾"]  # Alternative: circular spinner


# _SPIN_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]  # Alternative: braille spinner
class TurnSpinnerWidget(Widget):
    """Animated turn indicator spinner below the SP widget.

    Cycles through ◢ ◣ ◤ ◥ when it's the player's turn.
    Dimmed (grey42) when it's the enemy's turn.
    """

    DEFAULT_CSS = """
    TurnSpinnerWidget {
        width: 10;
        height: 1;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        is_player_turn: bool = True,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._is_player_turn = is_player_turn
        self._frame_idx = 0

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)

    # ── Public API ───────────────────────────────────

    def set_player_turn(self, active: bool) -> None:
        """Set whether it's the player's turn (shows spinner) or not (dimmed)."""
        self._is_player_turn = active
        self.refresh()

    # ── Internal ─────────────────────────────────────

    def _tick(self) -> None:
        if self._is_player_turn:
            self._frame_idx = (self._frame_idx + 1) % len(_SPIN_CHARS)
            self.refresh()

    def render(self) -> Text:
        char = _SPIN_CHARS[self._frame_idx]
        color = "cyan" if self._is_player_turn else "grey42"
        bold = self._is_player_turn
        return Text(char + " 我方行动" if self._is_player_turn else "对方行动", style=Style(color=color, bold=bold))
