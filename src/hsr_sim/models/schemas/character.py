from pydantic import BaseModel, Field
from .enums import StatType, Element
from .eidolon import EidolonConfig
from .skill import SkillConfig

class Memosprite(BaseModel):
    id: int
    name: str
    base_hp: float = Field(gt=0)
    base_atk: float = Field(gt=0)
    base_def: float = Field(gt=0)
    base_spd: float = Field(gt=0)
    memosprite_talent_id: int  # 忆灵天赋 ID
    memosprite_skill_id: int  # 忆灵技 ID


class CharacterConfig(BaseModel):
    id: int
    name: str
    rarity: int = Field(default=5, ge=4, le=5)
    element: Element
    base_hp: float = Field(gt=0)
    base_atk: float = Field(gt=0)
    base_def: float = Field(gt=0)
    base_spd: float = Field(gt=0)
    basic_atk: SkillConfig  # 普攻
    skill: SkillConfig  # 战技
    ultimate: SkillConfig  # 终结技
    eidolons: list[EidolonConfig] = []  # 星魂
    talent_ids: list[int] = []  # 天赋
    technique_id: int  # 秘技
    bonus_ability_ids: list[int] = []  # 额外能力
    stat_bonus: dict[StatType, float] = {}  # 行迹提供的角色固有属性加成
    elation_skill: int | None = None  # 欢愉技 ID
    memosprite: Memosprite | None = None  # 忆灵配置
