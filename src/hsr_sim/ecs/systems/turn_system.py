"""回合系统：HSR 行动值机制的核心实现。"""
from typing import Optional

import esper
from esper import Processor

from src.hsr_sim.ecs.components import (
    SpeedComponent,
    CharacterStatusComponent,
)
from src.hsr_sim.ecs.systems.action_queue import ActionQueue
from src.hsr_sim.models.character_status import CharacterStatus


class TurnSystem(Processor):
    """HSR 行动值系统：

    - action_value = 10000 / speed
    - 升序排列，最小值先行动
    - 行动后重新计算并回插队列
    - 全队减去下一行动者的值以保持一致性
    """

    # 浮点数比较精度
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

        for ent, (spd,
                  status) in esper.get_components(SpeedComponent,
                                                  CharacterStatusComponent):
            if status.status == CharacterStatus.ALIVE:
                action_value = 10000.0 / spd.value
                self.action_queue.push(ent, action_value)

        self._initialized = True
        self._advance_to_next_actor()

    def process(self):
        """每帧处理（暂无操作，行动推进由 BattleSession 主循环控制）。"""
        pass

    def _advance_to_next_actor(self) -> bool:
        """推进到下一个行动者。

        Returns:
            是否成功推进（队列非空）
        """
        next_actor = self.action_queue.peek_next()
        if next_actor is None:
            self.current_actor_id = None
            return False

        actor_id, _ = next_actor
        self.current_actor_id = actor_id

        # 检查是否倒下，若倒下则发布 TURN_SKIPPED 并继续下一位
        actor_status = esper.try_component(actor_id, CharacterStatusComponent)
        if actor_status and actor_status.status == CharacterStatus.KNOCKED_DOWN:
            self.action_queue.pop_next()  # 移除倒下角色
            self.event_stream.publish_turn_skipped_event(
                tick=self.current_tick,
                entity_id=actor_id,
                reason="knocked_down",
            )
            return self._advance_to_next_actor()  # 递归检查下一位

        # 发布行动决策事件
        self.event_stream.publish_action_decision_needed_event(
            tick=self.current_tick,
            actor_id=actor_id,
        )
        return True

    def on_action_finished(self):
        """标记当前行动完毕，推进到下一个行动者。

        由 BattleSession 在执行完成后调用。
        """
        if self.current_actor_id is None:
            return

        # 弹出当前行动者
        actor_id, _ = self.action_queue.pop_next()
        assert actor_id == self.current_actor_id, "队列与当前行动者不同步"

        # 获取当前行动者的速度，重新计算行动值
        spd = esper.try_component(actor_id, SpeedComponent)
        if spd:
            new_action_value = 10000.0 / spd.value
            self.action_queue.push(actor_id, new_action_value)

        # 获取下一个行动者的值，对全队进行归一化
        next_entry = self.action_queue.peek_next()
        if next_entry is not None:
            _, min_action_value = next_entry
            if min_action_value > self.EPSILON:
                self.action_queue.subtract_all(min_action_value)

        # 推进到下一行动者
        self._advance_to_next_actor()

    def on_speed_changed(self, entity_id: int, old_speed: float,
                         new_speed: float):
        """处理速度变更事件，重新计算该实体的行动值。

        由其他系统通过事件或直接调用触发。
        """
        # 由于我们使用了 mark_invalid 的延迟删除机制，
        # 我们可以简单地重新计算并重新插入
        # (实际上这需要一个更复杂的机制来追踪队列中的项)
        # MVP 版本中先不实现此功能，留作扩展
        pass

    def on_character_knocked_down(self, entity_id: int):
        """处理角色倒下事件，将其从行动队列中移除。

        由 HealthSystem 通过事件触发。
        """
        # 使用 mark_invalid 标记为无效，实际删除在 pop_next/peek_next 时完成
        self.action_queue.mark_invalid(entity_id)

    def on_character_knocked_down_restored(self, entity_id: int):
        """处理角色恢复事件，将其重新加入行动队列。

        由 HealingSystem 通过事件触发。
        """
        spd = esper.try_component(entity_id, SpeedComponent)
        if spd:
            action_value = 10000.0 / spd.value
            self.action_queue.push(entity_id, action_value)

    def get_current_actor(self) -> Optional[int]:
        """获取当前行动者 ID。"""
        return self.current_actor_id

    def set_current_tick(self, tick: int):
        """设置当前逻辑帧号，用于事件发布。"""
        self.current_tick = tick
