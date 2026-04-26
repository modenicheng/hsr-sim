from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget


class ActionBufferWidget(Widget):
    """FIFO action buffer display for ultimates/follow-up attacks.

    Shows pending actions that cut into the normal turn order.
    """

    DEFAULT_CSS = """
    ActionBufferWidget {
        width: 100%;
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._actions: list[str] = []

    def update_actions(self, actions: list[str]) -> None:
        self._actions = actions
        self.refresh()

    def render(self) -> Text:
        if not self._actions:
            return Text("")
        parts = [str(a) for a in self._actions]
        return Text(" ".join(parts), style=Style(color="#87CEEB"))
