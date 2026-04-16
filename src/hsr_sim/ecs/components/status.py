"""角色状态组件。"""
from pydantic import BaseModel

from src.hsr_sim.models.character_status import CharacterStatus


class CharacterStatusComponent(BaseModel):
    """角色当前战斗状态：ALIVE 或 KNOCKED_DOWN。"""

    status: CharacterStatus = CharacterStatus.ALIVE
