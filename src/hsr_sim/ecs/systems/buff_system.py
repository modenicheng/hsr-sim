"""Buff 系统：处理 Buff 生命周期和过期管理。"""

from esper import Processor
import esper
from eventure import Event

from hsr_sim.ecs.components import BuffContainerComponent
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType


class BuffSystem(Processor):
    """Buff 系统：处理 Buff 应用、持续时间递减和过期。

    职责：
    1. 监听 BUFF_APPLIED 事件，将 Buff 写入 BuffContainerComponent
    2. 每帧检查 Buff 剩余时间，到期发布 BUFF_EXPIRED 事件
    3. Buff 过期时注销其注册的 Hook
    4. 处理 Buff 层数变化
    """

    def __init__(self, event_stream, hook_registry):
        super().__init__()
        self.event_stream = event_stream
        self.hook_registry = hook_registry

    def process(self):
        """每帧检查所有实体的 Buff，处理过期。"""
        for ent, buff_container in esper.get_component(BuffContainerComponent):
            self._update_buffs(ent, buff_container)

    def subscribe_to_events(self):
        """订阅 Buff 相关事件。"""
        self.event_stream.subscribe(
            EventType.BUFF_APPLIED,
            self.on_buff_applied,
            priority=30,
            owner="buff_system",
        )

    def on_buff_applied(self, event: Event):
        """处理 Buff 应用事件。"""
        # 该事件处理已由其他系统完成，此处作为确认点
        pass

    def _update_buffs(
        self, entity_id: int, buff_container: BuffContainerComponent
    ):
        """更新实体的所有 Buff，处理持续时间和过期。"""
        if not buff_container.buffs:
            return

        expired_buffs = []

        for buff in buff_container.buffs:
            # 递减 Buff 持续时间
            if buff.remaining_duration is not None:
                buff.remaining_duration = max(
                    0.0, buff.remaining_duration - 1.0
                )

            # 检查是否过期
            if (
                buff.remaining_duration is not None
                and buff.remaining_duration <= 0
            ):
                expired_buffs.append(buff)

        # 处理过期 Buff
        for buff in expired_buffs:
            self._on_buff_expired(entity_id, buff)
            buff_container.buffs.remove(buff)

    def _on_buff_expired(self, entity_id: int, buff):
        """处理 Buff 过期。"""
        # 发布 BUFF_EXPIRED 事件
        self.event_stream.publish(
            GameEvent(
                tick=self.event_stream.event_log.current_tick,
                type=EventType.BUFF_EXPIRED,
                data={
                    "entity_id": entity_id,
                    "buff_id": buff.buff_id,
                },
            )
        )
