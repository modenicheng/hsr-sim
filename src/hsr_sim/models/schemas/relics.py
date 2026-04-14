from pydantic import BaseModel
from .enums import RelicSlot, StatType
from .passive import PassiveSkillConfig


# Data comes from https://honkai-star-rail.fandom.com/wiki/Relic/Stats
class RelicStatGrowth(BaseModel):
    max_value: float  # 该属性在当前部位的最大值
    growth_per_level: float  # 每强化等级增加的数值
    base_value: float  # 基础数值，未强化时的数值


# 遗器主属性成长（按星级）
RarityGrowthMap = dict[int, RelicStatGrowth]

MAIN_STAT_GROWTH_MAP: dict[StatType, RarityGrowthMap] = {
    StatType.SPEED: {
        5:
        RelicStatGrowth(base_value=4.032,
                        growth_per_level=1.4,
                        max_value=25.032),
        4:
        RelicStatGrowth(base_value=3.2256,
                        growth_per_level=1.1,
                        max_value=16.4256),
        3:
        RelicStatGrowth(base_value=2.4192,
                        growth_per_level=1.0,
                        max_value=11.4192),
        2:
        RelicStatGrowth(base_value=1.6128,
                        growth_per_level=1.0,
                        max_value=7.6128),
    },
    StatType.HP: {
        5:
        RelicStatGrowth(base_value=112.896,
                        growth_per_level=39.5136,
                        max_value=705.6),
        4:
        RelicStatGrowth(base_value=90.3168,
                        growth_per_level=31.61088,
                        max_value=469.6474),
        3:
        RelicStatGrowth(base_value=67.7376,
                        growth_per_level=23.70816,
                        max_value=281.111),
        2:
        RelicStatGrowth(base_value=45.1584,
                        growth_per_level=15.80544,
                        max_value=139.991),
    },
    StatType.ATK: {
        5:
        RelicStatGrowth(base_value=56.448,
                        growth_per_level=19.7568,
                        max_value=352.8),
        4:
        RelicStatGrowth(base_value=45.1584,
                        growth_per_level=15.80544,
                        max_value=234.8237),
        3:
        RelicStatGrowth(base_value=33.8688,
                        growth_per_level=11.85408,
                        max_value=140.5555),
        2:
        RelicStatGrowth(base_value=22.5792,
                        growth_per_level=7.90272,
                        max_value=69.9955),
    },
    StatType.HP_PERCENT: {
        5:
        RelicStatGrowth(base_value=0.06912,
                        growth_per_level=0.024192,
                        max_value=0.432),
        4:
        RelicStatGrowth(base_value=0.055296,
                        growth_per_level=0.019354,
                        max_value=0.287544),
        3:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.172107),
        2:
        RelicStatGrowth(base_value=0.027648,
                        growth_per_level=0.009677,
                        max_value=0.08571),
    },
    StatType.ATK_PERCENT: {
        5:
        RelicStatGrowth(base_value=0.06912,
                        growth_per_level=0.024192,
                        max_value=0.432),
        4:
        RelicStatGrowth(base_value=0.055296,
                        growth_per_level=0.019354,
                        max_value=0.287544),
        3:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.172107),
        2:
        RelicStatGrowth(base_value=0.027648,
                        growth_per_level=0.009677,
                        max_value=0.08571),
    },
    StatType.DEF_PERCENT: {
        5:
        RelicStatGrowth(base_value=0.0864,
                        growth_per_level=0.03024,
                        max_value=0.54),
        4:
        RelicStatGrowth(base_value=0.06912,
                        growth_per_level=0.024192,
                        max_value=0.359424),
        3:
        RelicStatGrowth(base_value=0.05184,
                        growth_per_level=0.018144,
                        max_value=0.215136),
        2:
        RelicStatGrowth(base_value=0.03456,
                        growth_per_level=0.012096,
                        max_value=0.107136),
    },
    StatType.BREAK_EFFECT: {
        5:
        RelicStatGrowth(base_value=0.10368,
                        growth_per_level=0.036277,
                        max_value=0.648),
        4:
        RelicStatGrowth(base_value=0.082944,
                        growth_per_level=0.02903,
                        max_value=0.431304),
        3:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.258165),
        2:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.128562),
    },
    StatType.EFFECT_HIT_RATE: {
        5:
        RelicStatGrowth(base_value=0.06912,
                        growth_per_level=0.024192,
                        max_value=0.432),
        4:
        RelicStatGrowth(base_value=0.055296,
                        growth_per_level=0.019354,
                        max_value=0.287544),
        3:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.172107),
        2:
        RelicStatGrowth(base_value=0.027648,
                        growth_per_level=0.009677,
                        max_value=0.08571),
    },
    StatType.ENERGY_REGEN: {
        5:
        RelicStatGrowth(base_value=0.031104,
                        growth_per_level=0.010886,
                        max_value=0.194394),
        4:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.129391),
        3:
        RelicStatGrowth(base_value=0.018662,
                        growth_per_level=0.006532,
                        max_value=0.07745),
        2:
        RelicStatGrowth(base_value=0.012442,
                        growth_per_level=0.004355,
                        max_value=0.038572),
    },
    StatType.OUTGOING_HEALING_BOOST: {
        5:
        RelicStatGrowth(base_value=0.055296,
                        growth_per_level=0.019354,
                        max_value=0.345606),
        4:
        RelicStatGrowth(base_value=0.044237,
                        growth_per_level=0.015483,
                        max_value=0.230033),
        3:
        RelicStatGrowth(base_value=0.033178,
                        growth_per_level=0.011612,
                        max_value=0.137686),
        2:
        RelicStatGrowth(base_value=0.022118,
                        growth_per_level=0.007741,
                        max_value=0.068564),
    },
    StatType.PHYSICAL_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.FIRE_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.ICE_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.WIND_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.LIGHTNING_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.QUANTUM_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.IMAGINARY_DMG: {
        5:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.388803),
        4:
        RelicStatGrowth(base_value=0.049766,
                        growth_per_level=0.017418,
                        max_value=0.258782),
        3:
        RelicStatGrowth(base_value=0.037325,
                        growth_per_level=0.013064,
                        max_value=0.154901),
        2:
        RelicStatGrowth(base_value=0.024883,
                        growth_per_level=0.008709,
                        max_value=0.077137),
    },
    StatType.CRIT_RATE: {
        5:
        RelicStatGrowth(base_value=0.05184,
                        growth_per_level=0.018144,
                        max_value=0.324),
        4:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.215652),
        3:
        RelicStatGrowth(base_value=0.031104,
                        growth_per_level=0.010886,
                        max_value=0.129078),
        2:
        RelicStatGrowth(base_value=0.020736,
                        growth_per_level=0.007258,
                        max_value=0.064284),
    },
    StatType.CRIT_DAMAGE: {
        5:
        RelicStatGrowth(base_value=0.10368,
                        growth_per_level=0.036288,
                        max_value=0.648),
        4:
        RelicStatGrowth(base_value=0.082944,
                        growth_per_level=0.02903,
                        max_value=0.431304),
        3:
        RelicStatGrowth(base_value=0.062208,
                        growth_per_level=0.021773,
                        max_value=0.258165),
        2:
        RelicStatGrowth(base_value=0.041472,
                        growth_per_level=0.014515,
                        max_value=0.128562),
    },
}

# 遗器主属性池，用于验证遗器主属性合法性，并提供按星级的成长数据
SLOT_STATS_MAP: dict[RelicSlot, list[tuple[StatType, RarityGrowthMap]]] = {
    RelicSlot.HEAD: [(StatType.HP, MAIN_STAT_GROWTH_MAP[StatType.HP])],
    RelicSlot.HANDS: [(StatType.ATK, MAIN_STAT_GROWTH_MAP[StatType.ATK])],
    RelicSlot.TORSO: [
        (StatType.HP_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT]),
        (StatType.ATK_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT]),
        (StatType.DEF_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT]),
        (StatType.EFFECT_HIT_RATE,
         MAIN_STAT_GROWTH_MAP[StatType.EFFECT_HIT_RATE]),
        (StatType.OUTGOING_HEALING_BOOST,
         MAIN_STAT_GROWTH_MAP[StatType.OUTGOING_HEALING_BOOST]),
        (StatType.CRIT_DAMAGE, MAIN_STAT_GROWTH_MAP[StatType.CRIT_DAMAGE]),
        (StatType.CRIT_RATE, MAIN_STAT_GROWTH_MAP[StatType.CRIT_RATE]),
    ],
    RelicSlot.FEET: [
        (StatType.SPEED, MAIN_STAT_GROWTH_MAP[StatType.SPEED]),
        (StatType.HP_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT]),
        (StatType.ATK_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT]),
        (StatType.DEF_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT]),
        (StatType.BREAK_EFFECT, MAIN_STAT_GROWTH_MAP[StatType.BREAK_EFFECT]),
    ],
    RelicSlot.PLANAR_SPHERE: [
        (StatType.HP_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT]),
        (StatType.ATK_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT]),
        (StatType.DEF_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT]),
        (StatType.PHYSICAL_DMG, MAIN_STAT_GROWTH_MAP[StatType.PHYSICAL_DMG]),
        (StatType.FIRE_DMG, MAIN_STAT_GROWTH_MAP[StatType.FIRE_DMG]),
        (StatType.ICE_DMG, MAIN_STAT_GROWTH_MAP[StatType.ICE_DMG]),
        (StatType.LIGHTNING_DMG, MAIN_STAT_GROWTH_MAP[StatType.LIGHTNING_DMG]),
        (StatType.WIND_DMG, MAIN_STAT_GROWTH_MAP[StatType.WIND_DMG]),
        (StatType.QUANTUM_DMG, MAIN_STAT_GROWTH_MAP[StatType.QUANTUM_DMG]),
        (StatType.IMAGINARY_DMG, MAIN_STAT_GROWTH_MAP[StatType.IMAGINARY_DMG]),
    ],
    RelicSlot.LINK_ROPE: [
        (StatType.HP_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT]),
        (StatType.ATK_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT]),
        (StatType.DEF_PERCENT, MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT]),
        (StatType.BREAK_EFFECT, MAIN_STAT_GROWTH_MAP[StatType.BREAK_EFFECT]),
        (StatType.ENERGY_REGEN, MAIN_STAT_GROWTH_MAP[StatType.ENERGY_REGEN]),
    ],
}

SubStatRoll = tuple[float, float, float]  # low / med / high

# 遗器副词条池（按星级）
# 数值单位：固定值使用绝对值；百分比使用小数（如 3.456% -> 0.03456）
# 注：来源表格中 2 星 DEF 的 Low 为 16.774（明显高于中/高档），此处按 ATK 对称值修正为 6.774
SUBSIDARY_STATS: dict[int, dict[StatType, SubStatRoll]] = {
    5: {
        StatType.SPEED: (2.0, 2.3, 2.6),
        StatType.HP: (33.87, 38.103755, 42.33751),
        StatType.ATK: (16.935, 19.051877, 21.168754),
        StatType.DEF: (16.935, 19.051877, 21.168754),
        StatType.HP_PERCENT: (0.03456, 0.03888, 0.0432),
        StatType.ATK_PERCENT: (0.03456, 0.03888, 0.0432),
        StatType.DEF_PERCENT: (0.0432, 0.0486, 0.054),
        StatType.BREAK_EFFECT: (0.05184, 0.05832, 0.0648),
        StatType.EFFECT_HIT_RATE: (0.03456, 0.03888, 0.0432),
        StatType.EFFECT_RES: (0.03456, 0.03888, 0.0432),
        StatType.CRIT_RATE: (0.02592, 0.02916, 0.0324),
        StatType.CRIT_DAMAGE: (0.05184, 0.05832, 0.0648),
    },
    4: {
        StatType.SPEED: (1.6, 1.8, 2.0),
        StatType.HP: (27.096, 30.483, 33.87),
        StatType.ATK: (13.548, 15.2415, 16.935),
        StatType.DEF: (13.548, 15.2415, 16.935),
        StatType.HP_PERCENT: (0.027648, 0.031104, 0.03456),
        StatType.ATK_PERCENT: (0.027648, 0.031104, 0.03456),
        StatType.DEF_PERCENT: (0.03456, 0.03888, 0.0432),
        StatType.BREAK_EFFECT: (0.041472, 0.046656, 0.05184),
        StatType.EFFECT_HIT_RATE: (0.027648, 0.031104, 0.03456),
        StatType.EFFECT_RES: (0.027648, 0.031104, 0.03456),
        StatType.CRIT_RATE: (0.020736, 0.023328, 0.02592),
        StatType.CRIT_DAMAGE: (0.041472, 0.046656, 0.05184),
    },
    3: {
        StatType.SPEED: (1.2, 1.3, 1.4),
        StatType.HP: (20.322, 22.862253, 25.402506),
        StatType.ATK: (10.161, 11.431126, 12.701252),
        StatType.DEF: (10.161, 11.431126, 12.701252),
        StatType.HP_PERCENT: (0.020736, 0.023328, 0.02592),
        StatType.ATK_PERCENT: (0.020736, 0.023328, 0.02592),
        StatType.DEF_PERCENT: (0.02592, 0.02916, 0.0324),
        StatType.BREAK_EFFECT: (0.031104, 0.034992, 0.03888),
        StatType.EFFECT_HIT_RATE: (0.020736, 0.023328, 0.02592),
        StatType.EFFECT_RES: (0.020736, 0.023328, 0.02592),
        StatType.CRIT_RATE: (0.015552, 0.017496, 0.01944),
        StatType.CRIT_DAMAGE: (0.031104, 0.034992, 0.03888),
    },
    2: {
        StatType.SPEED: (1.0, 1.1, 1.2),
        StatType.HP: (13.548, 15.2415, 16.935),
        StatType.ATK: (6.774, 7.62075, 8.4675),
        StatType.DEF: (6.774, 7.62075, 8.4675),
        StatType.HP_PERCENT: (0.013824, 0.015552, 0.01728),
        StatType.ATK_PERCENT: (0.013824, 0.015552, 0.01728),
        StatType.DEF_PERCENT: (0.01728, 0.01944, 0.0216),
        StatType.BREAK_EFFECT: (0.020736, 0.023328, 0.02592),
        StatType.EFFECT_HIT_RATE: (0.013824, 0.015552, 0.01728),
        StatType.EFFECT_RES: (0.013824, 0.015552, 0.01728),
        StatType.CRIT_RATE: (0.010368, 0.011664, 0.01296),
        StatType.CRIT_DAMAGE: (0.020736, 0.023328, 0.02592),
    },
}

# 副词条抽选权重（用于加权随机）
SUBSTAT_WEIGHT_MAP: dict[StatType, int] = {
    StatType.HP: 10,
    StatType.ATK: 10,
    StatType.DEF: 10,
    StatType.HP_PERCENT: 10,
    StatType.ATK_PERCENT: 10,
    StatType.DEF_PERCENT: 10,
    StatType.SPEED: 4,
    StatType.CRIT_RATE: 6,
    StatType.CRIT_DAMAGE: 6,
    StatType.EFFECT_HIT_RATE: 8,
    StatType.EFFECT_RES: 8,
    StatType.BREAK_EFFECT: 8,
}

class RelicSetConfig(BaseModel):
    id: int
    name: str
    # 2件套效果和4件套效果至少有一个不为 None
    passive_2_pc: PassiveSkillConfig # 2件套被动 必定有
    passive_4_pc: PassiveSkillConfig | None = None  # 4件套被动

class RelicConfig(BaseModel):
    id: int
    name: str
    relic_set: RelicSetConfig  # 遗器套装
    slot: RelicSlot
    story: str  # 背景故事
    # 这三个有关词条的不应该在这里写，它不属于遗器的固定属性，而是根据强化等级和随机抽选生成的动态属性
    # rarity: int = Field(default=5, ge=2, le=5)
    # main_stat: dict[StatType, float]  # 主属性，只有一个键值对
    # sub_stats: dict[StatType, float] = {}  # 副属性，可以有多个键值对

    # @model_validator(mode="after")
    # def validate_relic(self) -> Self:
    #     if not isinstance(self.main_stat, dict) or len(self.main_stat) != 1:
    #         raise ValueError(
    #             "main_stat must be a dict with exactly one key-value pair")

    #     stat_type, stat_value = next(iter(self.main_stat.items()))
    #     if stat_type not in dict(SLOT_STATS_MAP[self.slot]):
    #         raise ValueError(
    #             f"Invalid main_stat {stat_type} for slot {self.slot}")

    #     stat_growth = MAIN_STAT_GROWTH_MAP[stat_type][self.rarity]
    #     if stat_value > stat_growth.max_value:
    #         raise ValueError(
    #             f"main_stat {stat_type} value {stat_value} exceeds max value {stat_growth.max_value} for slot {self.slot} and rarity {self.rarity}."
    #         )
    #     if stat_value < stat_growth.base_value:
    #         raise ValueError(
    #             f"main_stat {stat_type} value {stat_value} is less than min value {stat_growth.base_value} for slot {self.slot} and rarity {self.rarity}."
    #         )

    #     if self.rarity == 2 and len(self.sub_stats) > 2:
    #         raise ValueError("2-star relics can have at most 2 sub-stats")
    #     elif len(self.sub_stats) > 4:
    #         raise ValueError("Relics can have at most 4 sub-stats")

    #     if stat_type in self.sub_stats:
    #         raise ValueError("Sub-stats cannot duplicate the main stat")

    #     return self
