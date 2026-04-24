from hsr_sim.models.db.battle_record import Battle, BattleRecord

from .base import BaseRepository


class BattleRepository(BaseRepository[Battle]):
    def __init__(self, db):
        super().__init__(Battle, db)

    def create_battle(self, time: int) -> Battle:
        return self.create(time=time)

    def add_record(
        self,
        battle_id: int | None,
        user_character_id: int,
        record_data: dict,
    ) -> BattleRecord:
        record = BattleRecord(
            battle_id=battle_id,
            user_character_id=user_character_id,
            record_data=record_data,
        )
        self.db.add(record)
        return record

    def list_records(self, battle_id: int) -> list[BattleRecord]:
        return self.db.query(BattleRecord).filter_by(battle_id=battle_id).all()

    def list_by_character(self, user_character_id: int) -> list[Battle]:
        return (
            self.db.query(Battle)
            .join(BattleRecord, BattleRecord.battle_id == Battle.id)
            .filter(BattleRecord.user_character_id == user_character_id)
            .all()
        )


class BattleRecordRepository(BaseRepository[BattleRecord]):
    def __init__(self, db):
        super().__init__(BattleRecord, db)

    def list_by_character(self, user_character_id: int) -> list[BattleRecord]:
        return self.list_by_filters(user_character_id=user_character_id)

    def list_by_battle(self, battle_id: int) -> list[BattleRecord]:
        return self.list_by_filters(battle_id=battle_id)
