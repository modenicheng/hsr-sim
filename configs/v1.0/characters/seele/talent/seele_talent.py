"""seele talent: 再现 (Resurgence).

When Seele defeats an enemy, she gains an extra action immediately.
During Resurgence, her damage is boosted by 80%.
"""

import esper
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.ecs.components import CharacterIdentityComponent
from hsr_sim.events.types import EventType
from hsr_sim.events.models import GameEvent


SEELE_CONFIG_ID = 10000000
RESURGENCE_DMG_BOOST = 1.80


class SeeleTalent(BaseSkill):
    def __init__(self, context):
        super().__init__(context)
        self._handle = None
        self.resurgence_active: bool = False
        self.resurgence_entity: int = -1

    def activate(self):
        if self._handle is not None:
            return
        self._handle = self.context.event_bus.subscribe(
            EventType.CHARACTER_KNOCKED_DOWN,
            self._on_enemy_defeated,
            priority=50,
            owner="seele_talent_resurgence",
        )

    def deactivate(self):
        if self._handle is not None:
            self.context.event_bus.unsubscribe(self._handle)
            self._handle = None

    def _on_enemy_defeated(self, event):
        data = self._event_data(event)
        source_id = data.get("source_id")
        if source_id is None or not self._is_seele(source_id):
            return

        entity_id = data.get("entity_id")
        if entity_id == source_id:
            return

        self.resurgence_active = True
        self.resurgence_entity = source_id

    def consume_resurgence(self, actor_id: int) -> bool:
        if not self.resurgence_active or self.resurgence_entity != actor_id:
            return False
        self.resurgence_active = False
        return True

    def get_dmg_multiplier(self) -> float:
        return RESURGENCE_DMG_BOOST

    @staticmethod
    def _is_seele(entity_id):
        identity = esper.try_component(entity_id, CharacterIdentityComponent)
        return identity is not None and identity.config_id == SEELE_CONFIG_ID

    @staticmethod
    def _event_data(event):
        if isinstance(event, GameEvent):
            return event.data
        return dict(getattr(event, "data", {}) or {})
