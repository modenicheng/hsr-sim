from collections.abc import Callable
from typing import Protocol, cast

from textual import events
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label

LOGO = [
    "█   █   ████  ████         ████  █████  █   █",
    "█░  █░ █ ░░░░ █░░░█       █ ░░░░  ░█░░░ ██ ██░",
    "█░  █░ █░     █░  █░      █░       █░   █░█ █░",
    "█████░  ███   ████ ░       ███     █░   █░█░█░",
    "█░░░█░   ░░█  █░█░░         ░░█    █░   █░ ░█░",
    "█░  █░     █░ █░ █            █░   █░   █░  █░",
    "█░  █░ ████ ░ █░  █       ████ ░ █████  █░  █░",
    " ░   ░  ░░░░   ░   ░       ░░░░   ░░░░░  ░   ░"
]


class HomeActionsApp(Protocol):

    def action_manage_characters(self) -> None: ...

    def action_manage_light_cones(self) -> None: ...

    def action_manage_relics(self) -> None: ...

    def action_start_battle_sim(self) -> None: ...
        # 跳转到战斗准备界面
        # 配置战斗信息后开始模拟

class HomeScreen(Screen):
    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }

    #home-body {
        width: 100%;
        max-width: 120;
        height: auto;
        padding: 1 2;
        align: center middle;
    }

    #logo {
        width: 100%;
        content-align: center middle;
        text-align: center;
        margin-bottom: 1;
    }

    #home-actions {
        width: 100%;
        height: auto;
        layout: grid;
        grid-size: 4 1;
        grid-columns: 1fr 1fr 1fr 1fr;
        grid-gutter: 1 1;
    }

    #home-actions.cols-2 {
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
    }

    #home-actions.cols-1 {
        grid-size: 1 4;
        grid-columns: 1fr;
    }

    #home-actions Button {
        width: 100%;
    }
    """

    BINDINGS = [("escape", "app.quit", "退出")]

    def compose(self):
        with Container(id="home-body"):
            yield Label("\n".join(LOGO), id="logo")
            with Container(id="home-actions"):
                yield Button("管理角色", id="btn-manage-characters", variant="primary")
                yield Button("管理光锥", id="btn-manage-light-cones")
                yield Button("管理遗器", id="btn-manage-relics")
                yield Button("开始战斗模拟", id="btn-start-battle", variant="success")

    def on_mount(self) -> None:
        self._update_action_layout(self.size.width)

    def on_resize(self, event: events.Resize) -> None:
        self._update_action_layout(event.size.width)

    def _update_action_layout(self, width: int) -> None:
        actions = self.query_one("#home-actions", Container)
        actions.remove_class("cols-1")
        actions.remove_class("cols-2")

        if width < 80:
            actions.add_class("cols-1")
        elif width < 120:
            actions.add_class("cols-2")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = cast(HomeActionsApp, self.app)
        button_actions = {
            "btn-manage-characters": app.action_manage_characters,
            "btn-manage-light-cones": app.action_manage_light_cones,
            "btn-manage-relics": app.action_manage_relics,
            "btn-start-battle": app.action_start_battle_sim,
        }
        action: Callable[[], None] | None
        action = button_actions.get(event.button.id or "")
        if action is not None:
            action()
