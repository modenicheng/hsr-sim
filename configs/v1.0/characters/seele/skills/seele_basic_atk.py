"""seele basic_atk script."""

from hsr_sim.skills.base_damage import BaseDamageSkill


class SeeleBasicAtk(BaseDamageSkill):

    # 技能特定属性
    damage_type = "quantum"  # 伤害类型（物理/元素/特殊）

    def calculate_damage(self, caster: int, target: int) -> float:
        
        return super().calculate_damage(caster, target)
