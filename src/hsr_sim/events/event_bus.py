from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from eventure import Event, EventBus, EventLog

from .models import GameEvent
from .types import EventType


@dataclass(slots=True, frozen=True)
class SubscriptionHandle:
    """事件订阅句柄。"""

    event_type: str
    callback_id: int
    owner: str | None = None


@dataclass(slots=True)
class _Subscriber:
    priority: int
    order: int
    callback: Callable[[Event], None]
    handle: SubscriptionHandle


class GameEventBus:
    """项目级事件总线薄封装。"""

    def __init__(self, bus: EventBus, event_log: EventLog):
        self._bus = bus
        self._event_log = event_log
        self._subscriptions: dict[str, list[_Subscriber]] = {}
        self._unsubscribe_hooks: dict[str, Callable[[], None]] = {}
        self._next_callback_id = 1
        self._next_order = 1

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    def _normalize_event_type(self, event_type: EventType | str) -> str:
        # 兼容不同导入路径下的同名 Enum（如 hsr_sim.* 与 src.hsr_sim.*）
        value = getattr(event_type, "value", None)
        if value is not None:
            return str(value)
        return str(event_type)

    def _ensure_tick(self, tick: int) -> None:
        if tick < self._event_log.current_tick:
            raise ValueError("event tick cannot go backwards")
        while self._event_log.current_tick < tick:
            self._event_log.advance_tick()

    def _fanout(self, event_type: str) -> Callable[[Event], None]:

        def _dispatch(event: Event) -> None:
            for subscriber in list(self._subscriptions.get(event_type, [])):
                subscriber.callback(event)

        return _dispatch

    def subscribe(
        self,
        event_type: EventType | str,
        handler: Callable[[Event], None],
        priority: int = 0,
        owner: str | None = None,
    ) -> SubscriptionHandle:
        event_name = self._normalize_event_type(event_type)
        if event_name not in self._subscriptions:
            self._subscriptions[event_name] = []
            self._unsubscribe_hooks[event_name] = self._bus.subscribe(
                event_name,
                self._fanout(event_name),
            )

        handle = SubscriptionHandle(
            event_type=event_name,
            callback_id=self._next_callback_id,
            owner=owner,
        )
        self._next_callback_id += 1
        self._subscriptions[event_name].append(
            _Subscriber(
                priority=priority,
                order=self._next_order,
                callback=handler,
                handle=handle,
            )
        )
        self._next_order += 1
        self._subscriptions[event_name].sort(
            key=lambda item: (-item.priority, item.order)
        )
        return handle

    def unsubscribe(self, handle: SubscriptionHandle) -> bool:
        subscribers = self._subscriptions.get(handle.event_type)
        if not subscribers:
            return False

        before = len(subscribers)
        subscribers[:] = [
            entry for entry in subscribers if entry.handle != handle
        ]
        removed = len(subscribers) != before
        if removed and not subscribers:
            unsubscribe = self._unsubscribe_hooks.pop(handle.event_type, None)
            if unsubscribe is not None:
                unsubscribe()
            self._subscriptions.pop(handle.event_type, None)
        return removed

    def unsubscribe_owner(self, owner: str) -> int:
        removed = 0
        for event_type in list(self._subscriptions):
            subscribers = self._subscriptions[event_type]
            before = len(subscribers)
            subscribers[:] = [
                entry for entry in subscribers if entry.handle.owner != owner
            ]
            removed += before - len(subscribers)
            if not subscribers:
                unsubscribe = self._unsubscribe_hooks.pop(event_type, None)
                if unsubscribe is not None:
                    unsubscribe()
                self._subscriptions.pop(event_type, None)
        return removed

    def publish(
        self,
        event: GameEvent,
        parent_event: Event | None = None,
    ) -> Event:
        self._ensure_tick(event.tick)
        eventure_event = event.to_eventure_event()
        if parent_event is not None:
            eventure_event.parent_id = parent_event.id

        self._event_log.events.append(eventure_event)
        self._bus.dispatch(eventure_event)
        return eventure_event

    def dispatch(self, event: Event | GameEvent) -> Event:
        if isinstance(event, GameEvent):
            return self.publish(event)

        self._ensure_tick(event.tick)
        self._event_log.events.append(event)
        self._bus.dispatch(event)
        return event

    def replay(self, events: Iterable[GameEvent | Event]) -> None:
        for event in events:
            self.dispatch(event)

    def publish_damage_event(
        self,
        *,
        tick: int,
        amount: int,
        source_id: int | None = None,
        target_id: int | None = None,
        critical: bool = False,
        damage_type: str | None = None,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        data: dict[str, Any] = {"amount": amount, "critical": critical}
        if source_id is not None:
            data["source_id"] = source_id
        if target_id is not None:
            data["target_id"] = target_id
        if damage_type is not None:
            data["damage_type"] = damage_type

        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.DAMAGE_DEALT,
                data=data,
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_skill_executed_event(
        self,
        *,
        tick: int,
        skill_name: str,
        source_id: int | None = None,
        target_id: int | None = None,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        data: dict[str, Any] = {"skill_name": skill_name}
        if source_id is not None:
            data["source_id"] = source_id
        if target_id is not None:
            data["target_id"] = target_id

        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.SKILL_EXECUTED,
                data=data,
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_character_knocked_down_event(
        self,
        *,
        tick: int,
        entity_id: int,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.CHARACTER_KNOCKED_DOWN,
                data={"entity_id": entity_id},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_character_knocked_down_restored_event(
        self,
        *,
        tick: int,
        entity_id: int,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.CHARACTER_KNOCKED_DOWN_RESTORED,
                data={"entity_id": entity_id},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_action_decision_needed_event(
        self,
        *,
        tick: int,
        actor_id: int,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.ACTION_DECISION_NEEDED,
                data={"actor_id": actor_id},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_turn_started_event(
        self,
        *,
        tick: int,
        entity_id: int,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.TURN_STARTED,
                data={"entity_id": entity_id},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_turn_ended_event(
        self,
        *,
        tick: int,
        entity_id: int,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.TURN_ENDED,
                data={"entity_id": entity_id},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_turn_skipped_event(
        self,
        *,
        tick: int,
        entity_id: int,
        reason: str = "knocked_down",
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.TURN_SKIPPED,
                data={"entity_id": entity_id, "reason": reason},
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )

    def publish_speed_changed_event(
        self,
        *,
        tick: int,
        entity_id: int,
        old_speed: float,
        new_speed: float,
        timestamp: float | None = None,
        parent_event: Event | None = None,
    ) -> Event:
        return self.publish(
            GameEvent(
                tick=tick,
                type=EventType.SPEED_CHANGED,
                data={
                    "entity_id": entity_id,
                    "old_speed": old_speed,
                    "new_speed": new_speed,
                },
                timestamp=timestamp,
            ),
            parent_event=parent_event,
        )
