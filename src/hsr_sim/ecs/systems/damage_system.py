"""伤害系统：处理伤害计算和 Hook 干预。"""

import random

import esper
from esper import Processor

from hsr_sim.ecs.components import (
    AttackComponent,
    CritDamageComponent,
    CritRateComponent,
    DefenseComponent,
)
from hsr_sim.hooks.hook_points import HookPoint


class DamageSystem(Processor):
    """伤害系统：只负责伤害计算流程与 Hook 干预。

    流程：
    1. Hook.BEFORE_DAMAGE_CALCULATION（传入原始伤害）
    2. 伤害公式计算（基础伤害、暴击、防御等）
    3. Hook.AFTER_DAMAGE_CALCULATION（最终伤害可被修改）
    4. 发布伤害结果事件，由 HealthSystem 处理 HP 扣除
    """

    def __init__(self, event_stream, hook_chain, current_tick_supplier):
        super().__init__()
        self.event_stream = event_stream
        self.hook_chain = hook_chain
        self.current_tick_supplier = current_tick_supplier

    def process(self):
        """系统在这里暂无操作。伤害由其他系统触发。"""
        pass

    def _determine_critical(
        self,
        attacker_id: int,
        defender_id: int,
        damage_type: str | None = None,
    ) -> tuple[bool, float, float]:
        """动态确定是否暴击，返回 (is_critical, final_crit_rate, final_crit_dmg)。

        流程：
        1. 从攻击者读取 CritRateComponent / CritDamageComponent
        2. 触发 BEFORE_CRIT_DETERMINATION hook 允许修改暴击率
        3. 与随机数比较确定暴击
        4. 暴击时使用 CritDamageComponent.value 作为暴击倍率
        """
        crit_rate_comp = esper.try_component(attacker_id, CritRateComponent)
        base_crit_rate = crit_rate_comp.value if crit_rate_comp else 0.05

        crit_dmg_comp = esper.try_component(attacker_id, CritDamageComponent)
        base_crit_dmg = crit_dmg_comp.value if crit_dmg_comp else 0.50

        hook_result = self.hook_chain.trigger(
            HookPoint.BEFORE_CRIT_DETERMINATION,
            base_crit_rate,
            attacker_id=attacker_id,
            target_id=defender_id,
            damage_type=damage_type,
        )
        final_crit_rate = (
            hook_result.value
            if hook_result.value is not None
            else base_crit_rate
        )

        is_critical = random.random() < final_crit_rate
        return is_critical, final_crit_rate, base_crit_dmg

    def calculate_and_apply_damage(
        self,
        attacker_id: int,
        defender_id: int,
        base_damage: float,
        damage_type: str | None = None,
        critical: bool | None = None,
    ) -> float:
        """计算并应用伤害。

        Args:
            attacker_id: 攻击者 ID
            defender_id: 防御者 ID
            base_damage: 基础伤害值
            damage_type: 伤害类型（可选）
            critical: 是否暴击（None 表示自动判定）

        Returns:
            最终伤害值（经 Hook 修改后）
        """
        # 暴击自动判定（当 critical 为 None 时）
        if critical is None:
            is_crit, _, crit_dmg = self._determine_critical(
                attacker_id,
                defender_id,
                damage_type=damage_type,
            )
            critical = is_crit
        else:
            crit_dmg = 0.5

        # 前置 Hook：BEFORE_DAMAGE_CALCULATION
        hook_result = self.hook_chain.trigger(
            HookPoint.BEFORE_DAMAGE_CALCULATION,
            base_damage,
            attacker_id=attacker_id,
            defender_id=defender_id,
            damage_type=damage_type,
            critical=critical,
        )

        damage_after_hook_before = (
            hook_result.value if hook_result.value is not None else base_damage
        )

        # 伤害公式计算
        final_damage = self._apply_damage_formula(
            damage_after_hook_before,
            attacker_id,
            defender_id,
            critical=critical,
            crit_damage=crit_dmg,
        )

        # 后置 Hook：AFTER_DAMAGE_CALCULATION
        hook_result = self.hook_chain.trigger(
            HookPoint.AFTER_DAMAGE_CALCULATION,
            final_damage,
            attacker_id=attacker_id,
            defender_id=defender_id,
            damage_type=damage_type,
            critical=critical,
        )

        final_damage = (
            hook_result.value if hook_result.value is not None else final_damage
        )

        # 确保伤害不为负
        final_damage = max(0, final_damage)

        # 发布伤害结果事件，由 HealthSystem 处理 HP 扣除
        self.event_stream.publish_damage_event(
            tick=self.current_tick_supplier(),
            amount=final_damage,
            source_id=attacker_id,
            target_id=defender_id,
            critical=critical,
            damage_type=damage_type,
        )

        return final_damage

    def _apply_damage_formula(
        self,
        base_damage: float,
        attacker_id: int,
        defender_id: int,
        critical: bool = False,
        crit_damage: float = 0.5,
    ) -> float:
        """应用伤害公式。

        简化版本：伤害 = 基础伤害 × (1 + 攻击力修正) × (1 - 防御修正)
        """
        # 获取攻击者的攻击力
        attacker_attack = esper.try_component(attacker_id, AttackComponent)
        attack_multiplier = 1.0
        if attacker_attack:
            attack_multiplier = 1.0 + (attacker_attack.value - 100) / 100 * 0.1

        # 获取防御者的防御力
        defender_defense = esper.try_component(defender_id, DefenseComponent)
        defense_reduction = 0.0
        if defender_defense:
            defense_reduction = defender_defense.value / (
                defender_defense.value + 200
            )

        damage = base_damage * attack_multiplier * (1 - defense_reduction)

        # 暴击伤害加成（使用 CritDamageComponent.value）
        if critical:
            damage *= 1.0 + crit_damage

        return damage
