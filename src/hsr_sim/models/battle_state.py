"""战斗状态、阶段和行动输入定义。"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class BattleState(str, Enum):
    """战斗全局状态。"""

    IDLE = "idle"
    PREPARING = "preparing"
    TURN_START = "turn_start"
    WAITING_ACTION = "waiting_action"
    EXECUTING_ACTION = "executing_action"
    TURN_END = "turn_end"
    FINISHED = "finished"


class ActionPhase(str, Enum):
    """行动执行阶段。"""

    IDLE = "idle"
    WAITING_DECISION = "waiting_decision"
    EXECUTING = "executing"
    FINISHED = "finished"


@dataclass
class ActionInput:
    """行动输入数据，来自玩家或 AI。"""

    actor_id: int
    action_type: str  # "basic", "skill", "ultimate", "talent", "technique"
    targets: list[int] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionDecision:
    """待执行行动决策，包含来源标识。"""

    action_input: ActionInput
    source: Literal["player", "ai"] = "ai"
