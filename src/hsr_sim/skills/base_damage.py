# src/hsr_sim/skills/base_damage.py
import esper

from .base import BaseSkill
from src.hsr_sim.ecs.components import AttackComponent
from src.hsr_sim.hooks.hook_points import HookPoint


class BaseDamageSkill(BaseSkill):
    """带伤害能力的技能基类，提供默认 ATK 模板"""

    # 子类可覆写的常量
    damage_type: str = "physical"  # 伤害类型，用于抗性计算

    def execute(self, caster: int, targets: list[int]) -> bool:
        """默认执行流程：检查资源 → 计算伤害 → 应用伤害 → 发布事件"""
        for target in targets:
            # 1. 计算基础伤害（子类可覆写）
            base_damage = self.calculate_damage(caster, target)

            # 2. 前置 Hook：BEFORE_SKILL_EXECUTION（允许修改伤害）
            hook_result = self.context.trigger_hook(
                HookPoint.BEFORE_SKILL_EXECUTION,
                base_damage,
                caster_id=caster,
                target_id=target,
                damage_type=self.damage_type,
            )

            final_damage = hook_result

            # 3. 后置 Hook（留作扩展）
            hook_result = self.context.trigger_hook(
                HookPoint.AFTER_SKILL_EXECUTION,
                final_damage,
                caster_id=caster,
                target_id=target,
                damage_type=self.damage_type,
            )

            final_damage = hook_result

            if final_damage > 0:
                # 4. 发布伤害事件（由 DamageSystem 和 HealthSystem 处理）
                self.context.publish_event(
                    "damage_dealt",
                    amount=final_damage,
                    source_id=caster,
                    target_id=target,
                    damage_type=self.damage_type,
                )

        return True

    def calculate_damage(self, caster: int, target: int) -> float:
        """默认伤害计算：攻击力 × 技能倍率。

        子类可覆写此方法实现特殊公式（如基于防御、生命值等）。
        """
        # 获取施法者攻击力
        atk_component = esper.try_component(caster, AttackComponent)
        if not atk_component:
            return 0.0

        # 获取伤害倍率（简化版：默认 1.0）
        multiplier = 1.0
        return atk_component.value * multiplier
