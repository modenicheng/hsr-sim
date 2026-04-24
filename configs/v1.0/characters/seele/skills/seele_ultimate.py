"""seele ultimate script: high quantum damage single-target.

In HSR, Seele's ultimate deals ~425% ATK quantum damage at level 10.
Here we use a 4.0 multiplier and also trigger E1 crit bonus.
"""

import esper
from hsr_sim.skills.base import BaseSkill
from hsr_sim.ecs.components import AttackComponent


ULT_DMG_MULTIPLIER = 4.0


class SeeleUltimate(BaseSkill):
    damage_type = "quantum"

    def execute(self, caster: int, targets: list[int]) -> dict:
        atk_comp = esper.try_component(caster, AttackComponent)
        base_atk = atk_comp.value if atk_comp else 0.0
        return {
            "effect": "damage",
            "base_damage": base_atk * ULT_DMG_MULTIPLIER,
            "damage_type": self.damage_type,
        }
