"""回合系统：HSR 行动值机制的核心实现。"""

from typing import Optional

import esper
from esper import Processor

from hsr_sim.ecs.components import (
    SpeedComponent,
    CharacterStatusComponent,
)
from hsr_sim.ecs.systems.action_queue import ActionQueue
from hsr_sim.models.character_status import CharacterStatus


class TurnSystem(Processor):
    """HSR 行动值系统：

    - action_value = 10000 / final_speed
    - 升序排列，最小值先行动
    - 行动后重置行动者 AV，全队减去其 time_cost，归一化后重新排序
    """

    TRACK_LENGTH = 10000.0
    EPSILON = 1e-6

    def __init__(self, event_stream):
        super().__init__()
        self.event_stream = event_stream
        self.action_queue = ActionQueue()
        self.current_actor_id: Optional[int] = None
        self.current_tick = 0
        self._initialized = False

    def initialize(self):
        """初始化时建立行动队列，为所有 ALIVE 实体计算初始行动值。"""
        if self._initialized:
            return

        for ent, (spd, status) in esper.get_components(
            SpeedComponent, CharacterStatusComponent
        ):
            if status.status == CharacterStatus.ALIVE:
                self.action_queue.push(ent, spd.action_value)

        self._normalize_queue()
        self._initialized = True
        self._advance_to_next_actor()

    def process(self):
        pass

    def _normalize_queue(self) -> None:
        """将队列中最小 AV 归一化为 0，其余实体同步减去该值。"""
        next_entry = self.action_queue.peek_next()
        if next_entry is not None:
            _, min_av = next_entry
            if min_av > self.EPSILON:
                self.action_queue.subtract_all(min_av)

    def _advance_to_next_actor(self) -> bool:
        next_actor = self.action_queue.peek_next()
        if next_actor is None:
            self.current_actor_id = None
            return False

        actor_id, _ = next_actor
        self.current_actor_id = actor_id

        actor_status = esper.try_component(actor_id, CharacterStatusComponent)
        if actor_status and actor_status.status == CharacterStatus.KNOCKED_DOWN:
            self.action_queue.pop_next()
            self.event_stream.publish_turn_skipped_event(
                tick=self.current_tick,
                entity_id=actor_id,
                reason="knocked_down",
            )
            return self._advance_to_next_actor()

        self.event_stream.publish_turn_started_event(
            tick=self.current_tick,
            entity_id=actor_id,
        )
        self.event_stream.publish_action_decision_needed_event(
            tick=self.current_tick,
            actor_id=actor_id,
        )
        return True

    def on_action_finished(self):
        """行动完毕结算：弹出行动者，其 time_cost 从全队扣除，再以新 AV 压回。"""
        if self.current_actor_id is None:
            return

        self.event_stream.publish_turn_ended_event(
            tick=self.current_tick,
            entity_id=self.current_actor_id,
        )

        actor_id, time_cost = self.action_queue.pop_next()
        assert actor_id == self.current_actor_id, "队列与当前行动者不同步"

        if time_cost > self.EPSILON:
            self.action_queue.subtract_all(time_cost)

        spd = esper.try_component(actor_id, SpeedComponent)
        if spd:
            self.action_queue.push(actor_id, spd.action_value)

        self._normalize_queue()
        self._advance_to_next_actor()

    def on_speed_changed(
        self, entity_id: int, old_speed: float, new_speed: float
    ):
        """处理速度变更：重新计算该实体的行动值并重新插入。

        当固定速度加成变化时调用（如获得/失去速度buff）。
        """
        spd = esper.try_component(entity_id, SpeedComponent)
        if spd:
            new_av = spd.action_value
            self.action_queue.reinsert(entity_id, new_av)

    def on_character_knocked_down(self, entity_id: int):
        self.action_queue.mark_invalid(entity_id)

    def on_character_knocked_down_restored(self, entity_id: int):
        spd = esper.try_component(entity_id, SpeedComponent)
        if spd:
            self.action_queue.reinsert(entity_id, spd.action_value)

    def get_current_actor(self) -> Optional[int]:
        return self.current_actor_id

    def set_current_tick(self, tick: int):
        self.current_tick = tick
