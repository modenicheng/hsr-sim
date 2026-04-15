import esper
from eventure import EventBus, EventLog

from hsr_sim.events.event_bus import GameEventBus
from hsr_sim.events.models import GameEvent
from hsr_sim.hooks import HookRegistry


class ECSWorld:

    def __init__(self, config_version: str):
        self.config_version = config_version
        self.world_name = config_version
        self._previous_world: str | None = None
        self.event_log = EventLog()
        self.event_bus = EventBus(event_log=self.event_log)
        self.event_stream = GameEventBus(
            bus=self.event_bus,
            event_log=self.event_log,
        )
        self.hook_registry = HookRegistry()
        self.systems: list[esper.Processor] = []
        # ... 初始化其他服务

    def activate(self):
        self._previous_world = esper.current_world
        esper.switch_world(self.world_name)
        for sys in self.systems:
            esper.add_processor(sys)

    def deactivate(self):
        if self._previous_world is not None:
            esper.switch_world(self._previous_world)
            self._previous_world = None

    def publish_event(self, event: GameEvent):
        return self.event_stream.publish(event)
