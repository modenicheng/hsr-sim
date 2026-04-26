from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget


class BuffDisplayWidget(Widget):
    """Compact buff icon row."""

    DEFAULT_CSS = """
    BuffDisplayWidget {
        height: 1;
        width: auto;
    }
    """

    def __init__(
        self,
        buffs: list[tuple[str, int]] | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.buffs: list[tuple[str, int]] = buffs or []

    def update_buffs(self, buffs: list[tuple[str, int]]) -> None:
        self.buffs = buffs
        self.refresh()

    def render(self) -> Text:
        if not self.buffs:
            return Text("")
        parts = []
        for name, stacks in self.buffs:
            if stacks > 1:
                parts.append(f"[{name} x{stacks}]")
            else:
                parts.append(f"[{name}]")
        return Text(" ".join(parts), style=Style(color="#87CEEB"))
