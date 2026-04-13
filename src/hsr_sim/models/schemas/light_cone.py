from pydantic import BaseModel, Field
from .enums import Path
from .passive import PassiveSkillConfig


class LightConeConfig(BaseModel):
    id: int
    name: str
    rarity: int = Field(default=5, ge=3, le=5)
    path: Path  # 命途
    superimposition: int = Field(default=1, ge=1, le=5)  # 叠影
    story: str  # 背景故事
    passive_skill: PassiveSkillConfig  # 被动技能脚本，描述被动技能效果和数值计算逻辑
