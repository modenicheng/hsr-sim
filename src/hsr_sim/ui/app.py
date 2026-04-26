from collections.abc import Iterable

from textual.app import App
from .state import AppState
from .screens.home import HomeScreen
from .screens.battle import BattleScreen
from textual.widget import Widget
from textual.widgets import Header, Footer


class HSRSimApp(App):
    SCREENS = {"home": HomeScreen, "battle": BattleScreen}

    def __init__(self):
        super().__init__()
        self.state = AppState()  # 全局状态

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("home")

    def action_manage_characters(self) -> None:
        self.notify("角色管理功能开发中", title="管理角色")

    def action_manage_light_cones(self) -> None:
        self.notify("光锥管理功能开发中", title="管理光锥")

    def action_manage_relics(self) -> None:
        self.notify("遗器管理功能开发中", title="管理遗器")

    def action_start_battle_sim(self) -> None:
        self.push_screen("battle")
