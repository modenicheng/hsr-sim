from hsr_sim.models.db.user_relics import UserRelic
from hsr_sim.repositories.relic_repo import RelicRepository


class RelicService:

    def __init__(self, relic_repo: RelicRepository):
        self.relic_repo = relic_repo

    def create_relic(
        self,
        set_id: int,
        slot: str,
        main_stat_type: str,
        version: str = "v1.0",
        level: int = 0,
        rarity: int = 5,
        sub_stats: list[dict] | None = None,
        equipped_by: int | None = None,
    ) -> UserRelic:
        """创建并持久化一个用户遗器实例。"""
        new_relic = UserRelic(
            version=version,
            set_id=set_id,
            slot=slot,
            level=level,
            rarity=rarity,
            main_stat_type=main_stat_type,
            sub_stats=sub_stats or [],
            equipped_by=equipped_by,
        )
        self.relic_repo.add(new_relic)
        self.relic_repo.db.commit()
        self.relic_repo.db.refresh(new_relic)
        return new_relic
