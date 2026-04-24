from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hsr_sim.services.config_loader import ConfigLoader
from src.hsr_sim.events.types import EventType


@dataclass(slots=True)
class SkillContext:
    """技能上下文依赖容器。"""

    world: Any = None
    event_bus: Any = None
    hook_chain: Any = None
    config_loader: ConfigLoader | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def trigger_hook(
        self, hook_point: str, initial_value: float, **kwargs
    ) -> float:
        """触发 Hook 的便捷方法。"""
        if self.hook_chain is None:
            return initial_value
        result = self.hook_chain.trigger(hook_point, initial_value, **kwargs)
        return result.value if result.value is not None else initial_value

    def publish_event(self, event_type: EventType | str, **kwargs) -> None:
        """发布事件的便捷方法。"""
        if self.event_bus is None:
            return
        # 简化版：直接发布事件
        from src.hsr_sim.events.models import GameEvent

        event = GameEvent(
            tick=0,  # 由调用者决定
            type=(
                event_type
                if isinstance(event_type, EventType)
                else EventType(event_type)
            ),
            data=kwargs,
        )
        self.event_bus.publish(event)


class BaseSkill:
    """技能脚本基类（可选）。"""

    def __init__(self, context: SkillContext):
        self.context = context
