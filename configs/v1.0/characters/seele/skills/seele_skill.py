"""seele skill script: 战技伤害 + SPD buff。"""

import esper
from hsr_sim.skills.base_damage import BaseDamageSkill
from hsr_sim.ecs.components import SpeedComponent, StackComponent
from hsr_sim.events.models import GameEvent
from hsr_sim.events.types import EventType


SPD_BUFF_AMOUNT = 25.0
STACK_TYPE = "seele_spd_boost"


class SeeleSkill(BaseDamageSkill):
    damage_type = "quantum"

    def __init__(self, context):
        super().__init__(context)
        self._turn_handle = None
        self._remaining_turns: dict[int, int] = {}

    def execute(self, caster: int, targets: list[int]) -> bool:
        self._ensure_stack(caster)
        result = super().execute(caster, targets)
        if result:
            self._ensure_cleanup_listener()
            self._apply_spd_buff(caster)
        return result

    def _ensure_stack(self, entity_id: int):
        stack = esper.try_component(entity_id, StackComponent)
        if stack and stack.stack_type == STACK_TYPE:
            return
        if stack is None:
            esper.add_component(
                entity_id,
                StackComponent(
                    stack_type=STACK_TYPE,
                    current=0,
                    max=1,
                ),
            )

    def _ensure_cleanup_listener(self):
        if self._turn_handle is not None:
            return
        self._turn_handle = self.context.event_bus.subscribe(
            EventType.TURN_ENDED,
            self._on_turn_ended,
            priority=50,
            owner="seele_skill_spd",
        )

    def _apply_spd_buff(self, entity_id: int):
        speed = esper.try_component(entity_id, SpeedComponent)
        if not speed:
            return

        stack = esper.try_component(entity_id, StackComponent)
        if not stack or stack.stack_type != STACK_TYPE:
            return

        speed.value -= SPD_BUFF_AMOUNT * stack.current
        new_stacks = min(stack.current + 1, stack.max)
        stack.current = new_stacks
        speed.value += SPD_BUFF_AMOUNT * new_stacks

        self._remaining_turns[entity_id] = 2

    def _on_turn_ended(self, event):
        data = self._event_data(event)
        entity_id = data.get("entity_id")
        if entity_id is None or entity_id not in self._remaining_turns:
            return

        remaining = self._remaining_turns[entity_id] - 1
        if remaining <= 0:
            del self._remaining_turns[entity_id]
            self._remove_buff(entity_id)
        else:
            self._remaining_turns[entity_id] = remaining

    def _remove_buff(self, entity_id: int):
        stack = esper.try_component(entity_id, StackComponent)
        if stack and stack.stack_type == STACK_TYPE:
            speed = esper.try_component(entity_id, SpeedComponent)
            if speed:
                speed.value -= SPD_BUFF_AMOUNT * stack.current
            esper.remove_component(entity_id, StackComponent)

    @staticmethod
    def _event_data(event):
        if isinstance(event, GameEvent):
            return event.data
        return dict(getattr(event, "data", {}) or {})
