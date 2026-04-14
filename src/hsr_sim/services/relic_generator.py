import random
from collections.abc import Sequence

from hsr_sim.models.db.user_relics import UserRelic
from hsr_sim.models.schemas.enums import RelicSlot, StatType
from hsr_sim.models.schemas.relics import SLOT_STATS_MAP, SUBSIDARY_STATS, SUBSTAT_WEIGHT_MAP
from hsr_sim.repositories.relic_repo import RelicRepository


class RelicGenerator:

    def __init__(
        self,
        relic_repo: RelicRepository,
        rng: random.Random | None = None,
    ):
        self.relic_repo = relic_repo
        self.rng = rng or random.Random()

    def generate(
        self,
        set_id: int,
        slot: RelicSlot | str,
        *,
        version: str = "v1.0",
        rarity: int = 5,
        level: int = 0,
        main_stat_type: StatType | str | None = None,
        sub_stat_count: int | None = None,
        equipped_by: int | None = None,
    ) -> UserRelic:
        slot_enum = RelicSlot(slot)
        main_stat = self._pick_main_stat(slot_enum, main_stat_type)
        sub_stats = self._generate_sub_stats(
            rarity=rarity,
            main_stat=main_stat,
            count=sub_stat_count,
        )

        relic = UserRelic(
            version=version,
            set_id=set_id,
            slot=slot_enum.value,
            level=level,
            rarity=rarity,
            main_stat_type=main_stat.value,
            sub_stats=sub_stats,
            equipped_by=equipped_by,
        )
        self.relic_repo.add(relic)
        self.relic_repo.db.commit()
        self.relic_repo.db.refresh(relic)
        return relic

    def _pick_main_stat(
        self,
        slot: RelicSlot,
        main_stat_type: StatType | str | None,
    ) -> StatType:
        candidates = [stat for stat, _ in SLOT_STATS_MAP[slot]]
        if main_stat_type is None:
            return self.rng.choice(candidates)

        desired = StatType(main_stat_type)
        if desired not in candidates:
            raise ValueError(
                f"Invalid main stat '{desired.value}' for slot '{slot.value}'"
            )
        return desired

    def _generate_sub_stats(
        self,
        *,
        rarity: int,
        main_stat: StatType,
        count: int | None,
    ) -> list[dict[str, int | str]]:
        stat_pool = SUBSIDARY_STATS.get(rarity)
        if stat_pool is None:
            raise ValueError(f"Unsupported rarity: {rarity}")

        available_stats = [stat for stat in stat_pool if stat != main_stat]
        if not available_stats:
            return []

        if count is None:
            count = self._default_sub_stat_count(rarity)
        count = max(0, min(count, len(available_stats)))

        selected_stats = self._weighted_sample_without_replacement(
            items=available_stats,
            weights=[SUBSTAT_WEIGHT_MAP.get(stat, 1) for stat in available_stats],
            k=count,
        )

        return [
            {
                "type": stat.value,
                "roll": self.rng.randint(0, 2),
            }
            for stat in selected_stats
        ]

    def _default_sub_stat_count(self, rarity: int) -> int:
        if rarity >= 5:
            return self.rng.choice([3, 4])
        if rarity == 4:
            return self.rng.choice([2, 3])
        if rarity == 3:
            return self.rng.choice([1, 2])
        return self.rng.choice([0, 1])

    def _weighted_sample_without_replacement(
        self,
        items: Sequence[StatType],
        weights: Sequence[int],
        k: int,
    ) -> list[StatType]:
        if k <= 0:
            return []

        pool_items = list(items)
        pool_weights = list(weights)
        selected: list[StatType] = []

        for _ in range(min(k, len(pool_items))):
            choice = self.rng.choices(pool_items, weights=pool_weights, k=1)[0]
            idx = pool_items.index(choice)
            selected.append(choice)
            pool_items.pop(idx)
            pool_weights.pop(idx)
        return selected
