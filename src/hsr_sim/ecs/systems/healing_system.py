"""治疗系统：处理治疗计算和 Hook 干预。"""

import esper
from esper import Processor

from src.hsr_sim.ecs.components import AttackComponent
from src.hsr_sim.events.models import GameEvent
from src.hsr_sim.events.types import EventType
from src.hsr_sim.hooks.hook_points import HookPoint


class HealingSystem(Processor):
    """治疗系统：只负责治疗计算流程与 Hook 干预。

    流程：
    1. Hook.BEFORE_HEALING_CALCULATION（传入原始治疗量）
    2. 治疗公式计算（基础治疗、治疗加成等）
    3. Hook.AFTER_HEALING_CALCULATION（最终治疗量可被修改）
    4. 发布治疗结果事件，由 HealthSystem 处理 HP 恢复
    """

    def __init__(self, event_stream, hook_chain, current_tick_supplier):
        super().__init__()
        self.event_stream = event_stream
        self.hook_chain = hook_chain
        self.current_tick_supplier = current_tick_supplier

    def process(self):
        """系统在这里暂无操作。治疗由其他系统触发。"""
        pass

    def calculate_and_apply_healing(
        self,
        healer_id: int,
        target_id: int,
        base_healing: float,
    ) -> float:
        """计算并应用治疗。

        Args:
            healer_id: 治疗者 ID
            target_id: 目标 ID
            base_healing: 基础治疗量

        Returns:
            最终治疗量（经 Hook 修改后）
        """
        # 前置 Hook：BEFORE_HEALING_CALCULATION
        hook_result = self.hook_chain.trigger(
            HookPoint.BEFORE_HEALING_CALCULATION,
            base_healing,
            healer_id=healer_id,
            target_id=target_id,
        )

        healing_after_hook_before = (
            hook_result.value if hook_result.value is not None else base_healing
        )

        # 治疗公式计算
        final_healing = self._apply_healing_formula(
            healing_after_hook_before,
            healer_id,
        )

        # 后置 Hook：AFTER_HEALING_CALCULATION
        hook_result = self.hook_chain.trigger(
            HookPoint.AFTER_HEALING_CALCULATION,
            final_healing,
            healer_id=healer_id,
            target_id=target_id,
        )

        final_healing = (
            hook_result.value
            if hook_result.value is not None
            else final_healing
        )

        # 确保治疗量不为负
        final_healing = max(0, final_healing)

        # 发布治疗结果事件，由 HealthSystem 处理 HP 恢复
        self.event_stream.publish(
            GameEvent(
                tick=self.current_tick_supplier(),
                type=EventType.HEALING_DONE,
                data={
                    "amount": final_healing,
                    "healer_id": healer_id,
                    "target_id": target_id,
                },
            )
        )

        return final_healing

    def _apply_healing_formula(
        self,
        base_healing: float,
        healer_id: int,
    ) -> float:
        """应用治疗公式。

        简化版本：治疗量 = 基础治疗 × (1 + 治疗者攻击力修正)
        """
        healer_attack = esper.try_component(healer_id, AttackComponent)
        healing_multiplier = 1.0
        if healer_attack:
            healing_multiplier = 1.0 + (healer_attack.value - 100) / 100 * 0.05

        healing = base_healing * healing_multiplier
        return healing
