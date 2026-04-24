"""seele eidolon 2: 蝶舞 — 战技的加速效果可叠加最多2层。"""

import esper
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.ecs.components import StackComponent
from hsr_sim.hooks import HookPoint


STACK_TYPE = "seele_spd_boost"


class SeeleEidolon2(BaseSkill):
    def activate(self):
        self._handle = self.context.hook_chain.register(
            HookPoint.AFTER_SKILL_EXECUTION,
            self._on_after_skill,
            priority=50,
            owner="seele_eidolon_2",
        )

    def deactivate(self):
        if self._handle is not None:
            self.context.hook_chain.unregister(
                HookPoint.AFTER_SKILL_EXECUTION, self._handle
            )

    def _on_after_skill(self, initial_value, caster_id, target_id, **kwargs):
        stack = esper.try_component(caster_id, StackComponent)
        if stack and stack.stack_type == STACK_TYPE:
            stack.max = 2
        return None
