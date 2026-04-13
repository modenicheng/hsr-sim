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
    """属性类型（用于角色属性、遗器主副词条、Buff等）"""
    HP = "hp"  # 生命值
    HP_PERCENT = "hp_percent"  # 生命值百分比
    ATK = "atk"  # 攻击
    ATK_PERCENT = "atk_percent"  # 攻击百分比
    DEF = "def"  # 防御
    DEF_PERCENT = "def_percent"  # 防御百分比
    SPEED = "speed"  # 速度
    CRIT_RATE = "crit_rate"  # 暴击率
    CRIT_DAMAGE = "crit_damage"  # 暴击伤害
    BREAK_EFFECT = "break_effect"  # 击破特攻
    ENERGY_REGEN = "energy_regen"  # 能量回复
    OUTGOING_HEALING_BOOST = "outgoing_healing_boost"  # 治疗加成
    EFFECT_HIT_RATE = "effect_hit_rate"  # 效果命中
    EFFECT_RES = "effect_res"  # 效果抵抗
    Elation = "elation"  # 欢愉度

    # 属性伤害加成
    PHYSICAL_DMG = "physical_dmg"
    FIRE_DMG = "fire_dmg"
    ICE_DMG = "ice_dmg"
    LIGHTNING_DMG = "lightning_dmg"
    WIND_DMG = "wind_dmg"
    QUANTUM_DMG = "quantum_dmg"
    IMAGINARY_DMG = "imaginary_dmg"

    # 元素抗性
    PHYSICAL_RES = "physical_res"
    FIRE_RES = "fire_res"
    ICE_RES = "ice_res"
    LIGHTNING_RES = "lightning_res"
    WIND_RES = "wind_res"
    QUANTUM_RES = "quantum_res"
    IMAGINARY_RES = "imaginary_res"


class SkillType(str, Enum):
    """技能类型"""
    BASIC = "basic"  # 普通攻击
    SKILL = "skill"  # 战技
    ULTIMATE = "ultimate"  # 大招
    TALENT = "talent"  # 天赋
    TECHNIQUE = "technique"  # 秘技
    MEMOSPRITE_SKILL = "memosprite_skill"
    MEMOSPRITE_TALENT = "memosprite_talent"
    ELATION = "elation"  # 欢愉技


class DMGType(str, Enum):
    """伤害类型"""
    PHYSICAL_DMG = "physical_dmg"  # 物理伤害
    FIRE_DMG = "fire_dmg"  # 火元素伤害
    ICE_DMG = "ice_dmg"  # 冰元素伤害
    LIGHTNING_DMG = "lightning_dmg"  # 雷元素伤害
    WIND_DMG = "wind_dmg"  # 风元素伤害
    QUANTUM_DMG = "quantum_dmg"  # 量子元素伤害
    IMAGINARY_DMG = "imaginary_dmg"  # 虚数元素伤害
    TRUE_DMG = "true_dmg"  # 真伤
    ELATION_DMG = "elation_dmg"  # 欢愉伤害


class SkillTargetType(str, Enum):
    """技能目标类型"""
    SINGLE_TARGET = "single_target"  # 单体
    BLAST = "blast"  # 扩散
    AOE = "aoe"  # 群攻


class TechniqueType(str, Enum):
    """秘技类型"""
    IMPAIR = "impair"  # 削弱
    SUPPORT = "support"  # 支援
    RESTORE = "restore"  # 回复
    ATTACK = "attack"  # 攻击
