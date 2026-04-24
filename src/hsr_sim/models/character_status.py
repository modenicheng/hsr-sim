"""角色状态枚举定义。"""

from enum import Enum


class CharacterStatus(str, Enum):
    """角色战斗状态。"""

    ALIVE = "alive"
    KNOCKED_DOWN = "knocked_down"
