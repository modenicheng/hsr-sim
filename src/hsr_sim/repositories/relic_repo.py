from hsr_sim.models.db.user_relics import UserRelic

from .base import BaseRepository


class UserRelicRepository(BaseRepository[UserRelic]):
    def __init__(self, db):
        super().__init__(UserRelic, db)

    def list_by_set_id(self, set_id: int) -> list[UserRelic]:
        return self.list_by_filters(set_id=set_id)

    def list_by_slot(self, slot: str) -> list[UserRelic]:
        return self.list_by_filters(slot=slot)

    def list_unequipped(self) -> list[UserRelic]:
        return (
            self.db.query(UserRelic)
            .filter(UserRelic.equipped_by.is_(None))
            .all()
        )

    def list_unequipped_by_slot(self, slot: str) -> list[UserRelic]:
        return (
            self.db.query(UserRelic)
            .filter(UserRelic.slot == slot, UserRelic.equipped_by.is_(None))
            .all()
        )

    def list_equipped_by_character(
        self,
        character_id: int,
    ) -> list[UserRelic]:
        return self.list_by_filters(equipped_by=character_id)

    def equip_to_character(
        self,
        relic_id: int,
        character_id: int,
    ) -> UserRelic | None:
        relic = self.get(relic_id)
        if relic is None:
            return None
        relic.equipped_by = character_id
        return relic

    def unequip(self, relic_id: int) -> UserRelic | None:
        relic = self.get(relic_id)
        if relic is None:
            return None
        relic.equipped_by = None
        return relic


class RelicRepository(UserRelicRepository):
    """兼容旧命名。"""

    def __init__(self, db):
        super().__init__(db)
