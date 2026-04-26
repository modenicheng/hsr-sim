from __future__ import annotations


from rich.text import Text
from rich.style import Style
from textual.widget import Widget


class ActionBarWidget(Widget):
    """Turn order display: sorted by action value, one entry per line.

    Renders vertically in a narrow column alongside the enemy area.
    """

    DEFAULT_CSS = """
    ActionBarWidget {
        width: 100%;
        height: auto;
        min-height: 1;
    }
    """

    def __init__(
        self,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._entries: list[tuple[int, str, float, float, bool]] = []
        self._current_actor: int | None = None

    def update_entries(
        self,
        entries: list[tuple[int, str, float, float, bool]],
        current_actor: int | None = None,
    ) -> None:
        """Update action bar entries.

        Args:
            entries: List of (entity_id, label, action_value, speed, is_enemy)
            current_actor: The entity_id currently taking action
        """
        self._entries = entries
        self._current_actor = current_actor
        self.refresh()

    def render(self) -> Text:
        if not self._entries:
            return Text("")

        line_width = 20
        dim_style = Style(dim=True)
        lines: list[Text] = []
        for eid, label, av, spd, is_enemy in self._entries:
            is_current = eid == self._current_actor
            marker = "▊" if is_current else "▎"

            if is_enemy:
                marker_style = Style(
                    color="#ff4444", bold=is_current
                )
                name_style = Style(color="white", bold=is_current)
            else:
                if is_current:
                    marker_style = Style(color="cyan", bold=True)
                    name_style = Style(color="cyan", bold=True)
                else:
                    marker_style = Style(color="cyan")
                    name_style = Style(color="white")

            av_str = f"{av:.0f}"
            av_pad = line_width - 2 - len(label) - len(av_str)
            lines.append(
                Text.assemble(
                    (marker, marker_style),
                    (label, name_style),
                    (" " * max(av_pad, 1), Style()),
                    (av_str, dim_style),
                )
            )

        return Text("\n").join(lines)
