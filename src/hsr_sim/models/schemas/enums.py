from enum import Enum


class Element(str, Enum):
    """角色/敌人的属性"""
    PHYSICAL = "physical"  # 物理
    FIRE = "fire"  # 火
    ICE = "ice"  # 冰
    LIGHTNING = "lightning"  # 雷
    WIND = "wind"  # 风
    QUANTUM = "quantum"  # 量子
    IMAGINARY = "imaginary"  # 虚数


class Path(str, Enum):
    """命途"""
    DESTRUCTION = "destruction"  # 毁灭
    HUNT = "hunt"  # 巡猎
    ERUDITION = "erudition"  # 智识
    HARMONY = "harmony"  # 同谐
    NIHILITY = "nihility"  # 虚无
    PRESERVATION = "preservation"  # 存护
    ABUNDANCE = "abundance"  # 丰饶
    REMEMBRANCE = "remembrance"  # 记忆
    ELATION = "elation"  # 欢愉


class RelicSlot(str, Enum):
    """遗器部位"""
    HEAD = "head"  # 头部
    HANDS = "hands"  # 手部
    TORSO = "torso"  # 护腿
    FEET = "feet"  # 鞋子
    PLANAR_SPHERE = "planar_sphere"  # 位面球
    LINK_ROPE = "link_rope"  # 连接绳


class StatType(str, Enum):
    """属性类型（用于遗器主副词条、Buff等）"""
    HP = "hp"
    HP_PERCENT = "hp_percent"
    ATK = "atk"
    ATK_PERCENT = "atk_percent"
    DEF = "def"
    DEF_PERCENT = "def_percent"
    SPEED = "speed"
    CRIT_RATE = "crit_rate"
    CRIT_DAMAGE = "crit_damage"
    BREAK_EFFECT = "break_effect"
    ENERGY_REGEN = "energy_regen"
    EFFECT_HIT_RATE = "effect_hit_rate"
    EFFECT_RES = "effect_res"

    # 属性伤害加成
    PHYSICAL_DMG = "physical_dmg"
    FIRE_DMG = "fire_dmg"
    ICE_DMG = "ice_dmg"
    LIGHTNING_DMG = "lightning_dmg"
    WIND_DMG = "wind_dmg"
    QUANTUM_DMG = "quantum_dmg"
    IMAGINARY_DMG = "imaginary_dmg"


class SkillType(str, Enum):
    """技能类型"""
    BASIC = "basic"
    SKILL = "skill"
    ULTIMATE = "ultimate"
    TALENT = "talent"
    TECHNIQUE = "technique"
