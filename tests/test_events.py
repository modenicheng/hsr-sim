from eventure import EventBus, EventLog

from hsr_sim.events import bus, event_log


def test_event_log_is_event_log():
    assert isinstance(event_log, EventLog)


def test_event_bus_is_event_bus():
    assert isinstance(bus, EventBus)


def test_event_bus_has_event_log():
    assert bus.event_log is event_log
