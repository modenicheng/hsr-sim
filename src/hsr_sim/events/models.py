from __future__ import annotations

import time
from typing import Any

from eventure import Event
from pydantic import BaseModel, ConfigDict, Field

from .types import EventType


class GameEvent(BaseModel):
    """项目级事件载荷。"""

    model_config = ConfigDict(extra="forbid")

    tick: int = Field(ge=0)
    type: EventType
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: float | None = None
    event_id: str | None = None
    parent_id: str | None = None

    def to_eventure_event(self) -> Event:
        """转换为 eventure 事件对象。"""
        payload: dict[str, Any] = {
            "tick": self.tick,
            "timestamp": (
                self.timestamp if self.timestamp is not None else time.time()
            ),
            "type": self.type.value,
            "data": self.data,
            "parent_id": self.parent_id,
        }
        if self.event_id is not None:
            payload["id"] = self.event_id
        return Event(**payload)

    @classmethod
    def from_eventure_event(cls, event: Event) -> "GameEvent":
        """从 eventure 事件对象恢复项目事件。"""
        return cls(
            tick=event.tick,
            timestamp=event.timestamp,
            type=EventType(event.type),
            data=dict(event.data),
            event_id=event.id,
            parent_id=event.parent_id,
        )
