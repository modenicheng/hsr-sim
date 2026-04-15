from eventure import Event, EventBus, EventLog

from hsr_sim.events.event_bus import GameEventBus
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType


def test_game_event_round_trip_to_eventure_event() -> None:
    event = GameEvent(
        tick=3,
        timestamp=123.456,
        type=EventType.DAMAGE_DEALT,
        data={"amount": 99},
        event_id="evt-1",
        parent_id="root",
    )

    eventure_event = event.to_eventure_event()
    restored = GameEvent.from_eventure_event(eventure_event)

    assert eventure_event.tick == 3
    assert eventure_event.timestamp == 123.456
    assert eventure_event.type == EventType.DAMAGE_DEALT.value
    assert eventure_event.data == {"amount": 99}
    assert eventure_event.id == "evt-1"
    assert eventure_event.parent_id == "root"
    assert restored == event


def test_game_event_bus_publish_records_and_dispatches_by_priority() -> None:
    event_log = EventLog()
    bus = EventBus(event_log=event_log)
    game_bus = GameEventBus(bus=bus, event_log=event_log)
    calls: list[str] = []

    def low_priority_handler(event: Event) -> None:
        calls.append(f"low:{event.data['amount']}")

    def high_priority_handler(event: Event) -> None:
        calls.append(f"high:{event.data['amount']}")

    game_bus.subscribe(
        EventType.DAMAGE_DEALT,
        low_priority_handler,
        priority=0,
    )
    game_bus.subscribe(
        EventType.DAMAGE_DEALT,
        high_priority_handler,
        priority=10,
    )

    published = game_bus.publish(
        GameEvent(
            tick=1,
            type=EventType.DAMAGE_DEALT,
            data={"amount": 42},
        )
    )

    assert calls == ["high:42", "low:42"]
    assert len(event_log.events) == 1
    assert event_log.events[0].type == EventType.DAMAGE_DEALT.value
    assert published.data == {"amount": 42}


def test_game_event_bus_publish_damage_event_helper() -> None:
    event_log = EventLog()
    bus = EventBus(event_log=event_log)
    game_bus = GameEventBus(bus=bus, event_log=event_log)

    published = game_bus.publish_damage_event(
        tick=2,
        amount=88,
        source_id=7,
        target_id=9,
        critical=True,
        damage_type="imaginary",
    )

    assert published.type == EventType.DAMAGE_DEALT.value
    assert published.data == {
        "amount": 88,
        "critical": True,
        "source_id": 7,
        "target_id": 9,
        "damage_type": "imaginary",
    }
    assert len(event_log.events) == 1
