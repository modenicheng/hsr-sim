from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.db.battle_record import Battle, BattleRecord
from hsr_sim.models.db.user_characters import UserCharacter


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return Session(engine)


def test_battle_user_character_many_to_many_bidirectional_query():
    session = _build_session()

    try:
        character = UserCharacter(char_config_id=1001, version="v1.0")
        battle = Battle(time=1_713_000_000)
        session.add_all([character, battle])
        session.flush()

        record = BattleRecord(
            battle_id=battle.id,
            user_character_id=character.id,
            record_data={"result": "win"},
        )
        session.add(record)
        session.commit()

        fetched_battle = session.get(Battle, battle.id)
        fetched_character = session.get(UserCharacter, character.id)

        assert fetched_battle is not None
        assert fetched_character is not None
        assert len(fetched_battle.user_characters) == 1
        assert fetched_battle.user_characters[0].id == character.id
        assert len(fetched_character.battles) == 1
        assert fetched_character.battles[0].id == battle.id
    finally:
        session.close()


def test_delete_battle_sets_battle_id_null_on_bridge_table():
    session = _build_session()

    try:
        character = UserCharacter(char_config_id=1002, version="v1.0")
        battle = Battle(time=1_713_000_100)
        session.add_all([character, battle])
        session.flush()

        record = BattleRecord(
            battle_id=battle.id,
            user_character_id=character.id,
            record_data={"damage": 9527},
        )
        session.add(record)
        session.commit()
        record_id = record.id

        session.delete(battle)
        session.commit()

        remaining_record = session.get(BattleRecord, record_id)
        assert remaining_record is not None
        assert remaining_record.battle_id is None
    finally:
        session.close()


def test_delete_user_character_cascades_bridge_row():
    session = _build_session()

    try:
        character = UserCharacter(char_config_id=1003, version="v1.0")
        battle = Battle(time=1_713_000_200)
        session.add_all([character, battle])
        session.flush()

        record = BattleRecord(
            battle_id=battle.id,
            user_character_id=character.id,
            record_data={"turns": 5},
        )
        session.add(record)
        session.commit()
        record_id = record.id

        session.delete(character)
        session.commit()

        assert session.get(BattleRecord, record_id) is None
    finally:
        session.close()
