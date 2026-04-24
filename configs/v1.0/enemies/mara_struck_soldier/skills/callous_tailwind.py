"""callous_tailwind: 200% ATK wind damage + Wind Shear."""

import esper
from hsr_sim.ecs.components import AttackComponent
from hsr_sim.skills.script_loader import BaseSkill


class CallousTailwind(BaseSkill):
    damage_type = "wind"

    def execute(self, caster: int, targets: list[int]) -> dict:
        atk_comp = esper.try_component(caster, AttackComponent)
        base_atk = atk_comp.value if atk_comp else 0.0
        return {
            "effect": "damage",
            "base_damage": base_atk * 2.0,
            "damage_type": self.damage_type,
        }
