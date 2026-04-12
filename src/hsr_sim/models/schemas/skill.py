from pydantic import BaseModel, Field
from .enums import SkillType

class SkillConfig(BaseModel):
    id: int
    name: str
    type: SkillType
    description: str
    target_type: str  # 技能目标类型，如单体、范围等
    energy_gain: float # 技能能量获取
    script: str  # 技能脚本，描述技能效果和数值计算逻辑