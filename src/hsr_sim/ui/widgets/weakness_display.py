from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget

ELEMENT_COLORS = {
    "physical": "#D1D2D1",
    "fire": "#F46953",
    "ice": "#83BCDD",
    "lightning": "#D37FE2",
    "wind": "#63CF9A",
    "quantum": "#5952C3",
    "imaginary": "#F5E253",
}

ELEMENT_SHORT = {
    "physical": "物",
    "fire": "火",
    "ice": "冰",
    "lightning": "雷",
    "wind": "风",
    "quantum": "量",
    "imaginary": "虚",
}


class WeaknessDisplayWidget(Widget):
    """Color-coded weakness type icons using single Chinese characters."""

    DEFAULT_CSS = """
    WeaknessDisplayWidget {
        height: 1;
        width: auto;
    }
    """

    def __init__(
        self,
        weakness_types: list[str] | None = None,
        disabled: bool = False,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.weakness_types = weakness_types or []
        self.disabled = disabled

    def update_weakness(
        self, weakness_types: list[str], disabled: bool = False
    ) -> None:
        self.weakness_types = weakness_types
        self.disabled = disabled
        self.refresh()

    def render(self) -> Text:
        result = Text()
        for w in self.weakness_types:
            short = ELEMENT_SHORT.get(w, w[:1])
            hex_color = ELEMENT_COLORS.get(w, "#FFFFFF")
            if self.disabled:
                result.append(short, style=Style(color="grey42"))
            else:
                result.append(short, style=Style(color=hex_color, bold=True))
        return result
