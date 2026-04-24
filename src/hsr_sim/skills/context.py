import esper
from typing import Any

from hsr_sim.hooks import HookChain
from hsr_sim.services.config_loader import ConfigLoader
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType


class SkillContext:
    def __init__(
        self,
        world,
        event_bus: Any,
        hook_chain: HookChain,
        config_loader: ConfigLoader,
        tick_supplier=None,
    ):
        self._world = world
        self._event_bus = event_bus
        self._hook_chain = hook_chain
        self._config_loader = config_loader
        self._tick_supplier = tick_supplier or (lambda: 0)

        self.caster: int | None = None
        self.targets: list[int] = []

    def publish_event(self, event_type: EventType | str, **kwargs):
        """发布事件的便捷方法，自动附加 caster 和 targets 信息。"""
        data = {**kwargs}
        if self.caster is not None:
            data["caster_id"] = self.caster
        if self.targets:
            data["target_ids"] = self.targets

        event = GameEvent(
            tick=self._tick_supplier(),
            type=event_type
            if isinstance(event_type, EventType)
            else EventType(event_type),
            data=data,
        )
        return self._event_bus.publish(event)

    def get_component(self, entity_id: int, component_type):
        """便捷获取实体组件。"""
        return esper.try_component(entity_id, component_type)

    def trigger_hook(self, hook_point, initial_value, **kwargs):
        """触发 Hook 并返回修改后的值。"""
        result = self._hook_chain.trigger(hook_point, initial_value, **kwargs)
        return result.value if result.value is not None else initial_value

    def get_config_loader(self) -> ConfigLoader:
        """获取配置加载器。"""
        return self._config_loader
