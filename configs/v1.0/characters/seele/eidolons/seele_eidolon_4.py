"""seele eidolon 4: 掠影"""

import esper
from hsr_sim.skills.script_loader import BaseSkill
from hsr_sim.ecs.components import CharacterIdentityComponent
from hsr_sim.ecs.systems.energy_system import EnergySystem
from hsr_sim.events.types import EventType

from src.hsr_sim.events.models import GameEvent


SEELE_CONFIG_ID = 10000000


class SeeleEidolon4(BaseSkill):
    def activate(self):
        self._handle = self.context.event_bus.subscribe(
            EventType.CHARACTER_KNOCKED_DOWN,
            self._on_enemy_defeated,
            priority=50,
            owner="seele_eidolon_4",
        )

    def deactivate(self):
        if self._handle is not None:
            self.context.event_bus.unsubscribe(self._handle)

    def _on_enemy_defeated(self, event):
        data = self._event_data(event)
        source_id = data.get("source_id")
        if source_id is not None and self._is_seele(source_id):
            EnergySystem.recover_energy(source_id, 15.0)

    @staticmethod
    def _event_data(event):
        if isinstance(event, GameEvent):
            return event.data
        return dict(getattr(event, "data", {}) or {})

    @staticmethod
    def _is_seele(entity_id):
        identity = esper.try_component(entity_id, CharacterIdentityComponent)
        return identity is not None and identity.config_id == SEELE_CONFIG_ID
