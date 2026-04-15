from enum import Enum


class EventType(str, Enum):
    """事件类型常量。"""

    DAMAGE_DEALT = "damage_dealt"
    SKILL_EXECUTED = "skill_executed"
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    BUFF_APPLIED = "buff_applied"
    BUFF_EXPIRED = "buff_expired"
    HEALING_DONE = "healing_done"
    ENERGY_CHANGED = "energy_changed"
