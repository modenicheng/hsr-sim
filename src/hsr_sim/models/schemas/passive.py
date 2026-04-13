from pydantic import BaseModel


class PassiveSkillConfig(BaseModel):
    id: int
    name: str
    description: str
    script: str  # 被动技能脚本，描述被动技能效果和数值计算逻辑
