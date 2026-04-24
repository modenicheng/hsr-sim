# services/stat_calculator.py
from collections import defaultdict
from hsr_sim.models.schemas.relics import MAIN_STAT_GROWTH_MAP, SUBSIDARY_STATS
from hsr_sim.models.schemas.enums import StatType
from hsr_sim.repositories.relic_repo import RelicRepository
from hsr_sim.utils import SessionLocal
from hsr_sim.logger import get_logger
from hsr_sim.ecs.components.equipment import EquippedRelicsComponent

logger = get_logger(__name__)


def calculate_relic_stats(relic_ids: list[int]) -> dict[StatType, float]:
    """计算遗器提供的总属性加成

    Args:
        relic_ids (list[int]): 遗器实例ID列表

    Returns:
        dict[StatType, float]: 各属性的总加成值字典，其中：
            - key (StatType): 属性类型枚举值，如生命值、攻击力、防御力、速度等
            - value (float): 该属性的总加成数值，包含所有遗器主词条和副词条的累加值
            如果遗器ID在数据库中不存在，将跳过该遗器并记录警告日志。
            若所有遗器ID都无效，将返回空字典。
    """
    total = defaultdict(float)
    with SessionLocal() as db:
        relic_repo = RelicRepository(db)
        for rid in relic_ids:
            relic = relic_repo.get(rid)
            if relic is None:
                logger.warning(f"Relic with id {rid} not found in database.")
                continue  # 或者抛出异常
            # 主词条计算
            growth = MAIN_STAT_GROWTH_MAP[StatType(relic.main_stat_type)][
                relic.rarity
            ]
            main_value = (
                growth.base_value + growth.growth_per_level * relic.level
            )
            total[StatType(relic.main_stat_type)] += main_value

            # 副词条计算
            sub_pool = SUBSIDARY_STATS[relic.rarity]
            for sub in relic.sub_stats:
                stat_type = StatType(sub["type"])
                roll = sub["roll"]  # 0,1,2
                value = sub_pool[stat_type][roll]
                total[stat_type] += value
    return total


def calculate_equipped_relic_stats(
    equipped_relics: EquippedRelicsComponent,
) -> dict[StatType, float]:
    """计算角色当前装备的遗器提供的总属性加成"""
    relic_ids = [
        rid
        for rid in [
            equipped_relics.head,
            equipped_relics.hands,
            equipped_relics.torso,
            equipped_relics.feet,
            equipped_relics.planar_sphere,
            equipped_relics.link_rope,
        ]
        if rid is not None
    ]
    return calculate_relic_stats(relic_ids)
