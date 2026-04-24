"""mara_struck_soldier passive: Rejuvenate — first KO: revive at 50% HP.

Uses the BEFORE_CHARACTER_KNOCKED_DOWN hook to intercept KO events.
First death: restore 50% HP, prevent KO event, increment counter.
Second death: let the KO proceed (permanently removed).
"""

import esper
from hsr_sim.ecs.components import CharacterStatusComponent, HealthComponent
from hsr_sim.hooks.hook_points import HookPoint
from hsr_sim.hooks.hook_protocol import HookResult
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.skills.script_loader import BaseSkill


class MaraStruckSoldierPassive(BaseSkill):
    def __init__(self, context):
        super().__init__(context)
        self._death_count: dict[int, int] = {}
        self._handle = None

    def activate(self):
        if self._handle is not None:
            return
        self._handle = self.context.hook_chain.register(
            HookPoint.BEFORE_CHARACTER_KNOCKED_DOWN,
            self._on_before_knocked_down,
            priority=50,
            owner="mara_struck_soldier_rejuvenate",
        )

    def deactivate(self):
        if self._handle is not None:
            self.context.hook_chain.unregister(
                HookPoint.BEFORE_CHARACTER_KNOCKED_DOWN, self._handle
            )
            self._handle = None

    def _on_before_knocked_down(
        self, current_value, entity_id, source_id=None, **kwargs
    ):
        status = esper.try_component(entity_id, CharacterStatusComponent)
        if status is None or status.status == CharacterStatus.KNOCKED_DOWN:
            return None

        health = esper.try_component(entity_id, HealthComponent)
        if health is None:
            return None

        count = self._death_count.get(entity_id, 0)
        if count == 0:
            self._death_count[entity_id] = 1
            health.value = health.max_value * 0.5
            status.status = CharacterStatus.ALIVE
            self.context.event_bus.publish_character_knocked_down_restored_event(
                tick=0, entity_id=entity_id,
            )
            return HookResult(stop=True)

        return None
