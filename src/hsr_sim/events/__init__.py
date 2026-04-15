from eventure import EventBus, EventLog

from hsr_sim.events.event_bus import GameEventBus
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType

event_log = EventLog()
bus = EventBus(event_log=event_log)
game_bus = GameEventBus(bus=bus, event_log=event_log)

__all__ = ["EventType", "GameEvent", "GameEventBus", "bus", "event_log", "game_bus"]
