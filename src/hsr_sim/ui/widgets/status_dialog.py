from __future__ import annotations

from rich.table import Table
from rich.panel import Panel
from rich import box
from textual.screen import ModalScreen
from textual.widgets import Static


class StatusDialog(ModalScreen[None]):
    """Modal dialog showing detailed character or enemy stats."""

    DEFAULT_CSS = """
    StatusDialog {
        align: center middle;
    }

    StatusDialog Static {
        width: auto;
        max-width: 60;
        height: auto;
        background: $surface;
        border: solid $border;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "关闭"),
    ]

    def __init__(self, title: str, data: dict[str, str | float | int]) -> None:
        super().__init__()
        self._title = title
        self._data = data

    def compose(self):
        table = Table(title=self._title, box=box.ROUNDED, show_header=False)
        table.add_column("属性", style="cyan", no_wrap=True)
        table.add_column("值", style="white")
        for key, val in self._data.items():
            table.add_row(key, str(val))
        yield Static(Panel(table, border_style="cyan"))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
