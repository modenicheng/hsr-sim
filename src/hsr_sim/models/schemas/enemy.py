from pydantic import BaseModel, Field
from .enums import Element
from .skill import EnemySkillConfig
from .passive import PassiveSkillConfig


class EnemyConfig(BaseModel):
    id: int
    name: str
    base_hp: float = Field(gt=0)
    base_atk: float = Field(gt=0)
    base_def: float = Field(gt=0)
    base_spd: float = Field(gt=0)
    base_weakness: list[Element] | None = None  # 可能可变
    toughness: int = Field(default=0, ge=0)  # 韧性值

    skills: list[EnemySkillConfig] = []
    passives: list[PassiveSkillConfig] = []
