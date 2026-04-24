"""血量系统：处理 HP 变化、倒下判定和复活恢复。"""

import esper
from esper import Processor
from eventure import Event

from hsr_sim.ecs.components import (
    HealthComponent,
    CharacterStatusComponent,
)
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType
from hsr_sim.hooks.hook_points import HookPoint
from hsr_sim.models.character_status import CharacterStatus


class HealthSystem(Processor):
    """血量系统：HP 唯一写入口。

    职责：
    1. 监听 DAMAGE_DEALT 事件，扣除 HP
    2. 监听 HEALING_DONE 事件，恢复 HP
    3. HP <= 0 时，设状态为 KNOCKED_DOWN，发布 CHARACTER_KNOCKED_DOWN 事件
    4. 从 KNOCKED_DOWN 恢复时，设状态为 ALIVE，发布 CHARACTER_KNOCKED_DOWN_RESTORED 事件
    """

    def __init__(self, event_stream, hook_registry=None):
        super().__init__()
        self.event_stream = event_stream
        self.hook_registry = hook_registry

    def process(self):
        """系统在这里暂无操作。HP 变化由事件驱动。"""
        pass

    def subscribe_to_events(self):
        """订阅伤害和治疗事件。"""
        self.event_stream.subscribe(
            EventType.DAMAGE_DEALT,
            self.on_damage_dealt,
            priority=50,
            owner="health_system",
        )
        self.event_stream.subscribe(
            EventType.HEALING_DONE,
            self.on_healing_done,
            priority=50,
            owner="health_system",
        )

    def on_damage_dealt(self, event: Event):
        """处理伤害事件，扣除 HP。"""
        data = self._event_data(event)
        target_id = data.get("target_id")
        amount = data.get("amount", 0)
        source_id = data.get("source_id")

        if target_id is None or amount <= 0:
            return

        self._apply_damage(target_id, amount, source_id=source_id)

    def on_healing_done(self, event: Event):
        """处理治疗事件，恢复 HP。"""
        data = self._event_data(event)
        target_id = data.get("target_id")
        amount = data.get("amount", 0)

        if target_id is None or amount <= 0:
            return

        self._apply_healing(target_id, amount)

    def _event_data(self, event: Event | GameEvent) -> dict:
        """兼容 GameEvent / eventure.Event，统一提取 data 字段。"""
        if isinstance(event, GameEvent):
            return event.data
        return dict(getattr(event, "data", {}) or {})

    def _apply_damage(
        self, entity_id: int, damage: float, source_id: int | None = None
    ):
        """应用伤害，扣除 HP。"""
        health = esper.try_component(entity_id, HealthComponent)
        if not health:
            return

        health.value = max(0, health.value - damage)

        # 检查是否倒下
        if health.value <= 0:
            self._set_knocked_down(entity_id, source_id=source_id)

    def _apply_healing(self, entity_id: int, healing: float):
        """应用治疗，恢复 HP。"""
        health = esper.try_component(entity_id, HealthComponent)
        status = esper.try_component(entity_id, CharacterStatusComponent)

        if not health:
            return

        old_value = health.value
        health.value = min(health.max_value, health.value + healing)

        # 如果从倒下状态恢复，设为 ALIVE
        if (
            status
            and status.status == CharacterStatus.KNOCKED_DOWN
            and health.value > 0
        ):
            self._set_alive(entity_id)

    def _set_knocked_down(self, entity_id: int, source_id: int | None = None):
        """设置角色为倒下状态。

        先触发 BEFORE_CHARACTER_KNOCKED_DOWN hook，允许外部逻辑
        （如敌人复活被动）拦截并阻止击倒事件。
        """
        status = esper.try_component(entity_id, CharacterStatusComponent)
        if not status or status.status == CharacterStatus.KNOCKED_DOWN:
            return

        if self.hook_registry is not None:
            hook_result = self.hook_registry.trigger(
                HookPoint.BEFORE_CHARACTER_KNOCKED_DOWN,
                None,
                entity_id=entity_id,
                source_id=source_id,
            )
            if hook_result.stop:
                return

        status.status = CharacterStatus.KNOCKED_DOWN

        data = {"entity_id": entity_id}
        if source_id is not None:
            data["source_id"] = source_id

        self.event_stream.publish(
            GameEvent(
                tick=self.event_stream.event_log.current_tick,
                type=EventType.CHARACTER_KNOCKED_DOWN,
                data=data,
            ),
        )

    def _set_alive(self, entity_id: int):
        """设置角色为存活状态。"""
        status = esper.try_component(entity_id, CharacterStatusComponent)
        if status and status.status == CharacterStatus.KNOCKED_DOWN:
            status.status = CharacterStatus.ALIVE

            # 发布 CHARACTER_KNOCKED_DOWN_RESTORED 事件
            self.event_stream.publish_character_knocked_down_restored_event(
                tick=self.event_stream.event_log.current_tick,
                entity_id=entity_id,
            )
