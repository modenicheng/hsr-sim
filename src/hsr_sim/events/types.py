from enum import Enum


class EventType(str, Enum):
    """事件类型常量。"""

    # 原有事件类型
    DAMAGE_DEALT = "damage_dealt"
    SKILL_EXECUTED = "skill_executed"
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    BUFF_APPLIED = "buff_applied"
    BUFF_EXPIRED = "buff_expired"
    HEALING_DONE = "healing_done"
    ENERGY_CHANGED = "energy_changed"

    # 战斗调度事件
    ACTION_DECISION_NEEDED = "action_decision_needed"
    ACTION_EXECUTION_STARTED = "action_execution_started"
    ACTION_EXECUTION_FINISHED = "action_execution_finished"
    TURN_CYCLE_COMPLETE = "turn_cycle_complete"
    BATTLE_RESULT_DETERMINED = "battle_result_determined"

    # 角色状态事件
    CHARACTER_KNOCKED_DOWN = "character_knocked_down"
    CHARACTER_KNOCKED_DOWN_RESTORED = "character_knocked_down_restored"
    TURN_SKIPPED = "turn_skipped"

    # 属性变更事件
    SPEED_CHANGED = "speed_changed"
