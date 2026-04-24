"""seele eidolon 1: 斩尽"""

import esper
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.ecs.components import HealthComponent, CharacterIdentityComponent
from hsr_sim.hooks import HookPoint


SEELE_CONFIG_ID = 10000000


class SeeleEidolon1(BaseSkill):
    def activate(self):
        self._handle = self.context.hook_chain.register(
            HookPoint.BEFORE_CRIT_DETERMINATION,
            self._on_crit,
            priority=50,
            owner="seele_eidolon_1",
        )

    def deactivate(self):
        if self._handle is not None:
            self.context.hook_chain.unregister(
                HookPoint.BEFORE_CRIT_DETERMINATION, self._handle
            )

    def _on_crit(self, current_crit_rate, attacker_id, target_id, **kwargs):
        identity = esper.try_component(attacker_id, CharacterIdentityComponent)
        if identity is None or identity.config_id != SEELE_CONFIG_ID:
            return None
        health = esper.try_component(target_id, HealthComponent)
        if health is not None and health.value / health.max_value <= 0.8:
            return current_crit_rate + 0.15
        return None
