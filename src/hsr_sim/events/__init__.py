from eventure import EventBus, EventLog

event_log = EventLog()
bus = EventBus(event_log=event_log)

__all__ = ["bus", "event_log"]
