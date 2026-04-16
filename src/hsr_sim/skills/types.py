"""技能类型枚举。"""
from enum import Enum


class SkillType(str, Enum):
    """技能类型分类。"""

    BASIC = "basic"  # 普通攻击
    SKILL = "skill"  # 技能
    ULTIMATE = "ultimate"  # 终极
    TALENT = "talent"  # 天赋
    TECHNIQUE = "technique"  # 秘技
