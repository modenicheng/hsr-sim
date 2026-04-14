from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.db.user_relics import UserRelic
from hsr_sim.repositories.battle_repo import BattleRepository
from hsr_sim.repositories.character_repo import UserCharacterRepository
from hsr_sim.repositories.light_cone_repo import UserLightConeRepository
from hsr_sim.repositories.relic_repo import UserRelicRepository


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_relic_repo_list_unequipped_by_slot():
    session = _build_session()
    try:
        repo = UserRelicRepository(session)
        relic_1 = UserRelic(
            set_id=1,
            slot="head",
            main_stat_type="hp",
            rarity=5,
            level=0,
            sub_stats=[],
            equipped_by=None,
        )
        relic_2 = UserRelic(
            set_id=1,
            slot="head",
            main_stat_type="hp",
            rarity=5,
            level=0,
            sub_stats=[],
            equipped_by=100,
        )
        relic_3 = UserRelic(
            set_id=1,
            slot="hands",
            main_stat_type="atk",
            rarity=5,
            level=0,
            sub_stats=[],
            equipped_by=None,
        )
        session.add_all([relic_1, relic_2, relic_3])
        session.commit()

        heads = repo.list_unequipped_by_slot("head")

        assert len(heads) == 1
        assert heads[0].id == relic_1.id
    finally:
        session.close()


def test_light_cone_repo_list_unequipped():
    session = _build_session()
    try:
        lc_repo = UserLightConeRepository(session)
        char_repo = UserCharacterRepository(session)

        char = char_repo.create(char_config_id=1001, version="v1.0")
        equipped = lc_repo.create(config_id=2001, version="v1.0")
        free = lc_repo.create(config_id=2002, version="v1.0")
        session.flush()

        char.equipped_light_cone_id = equipped.id
        session.commit()

        unequipped = lc_repo.list_unequipped()
        assert [lc.id for lc in unequipped] == [free.id]
    finally:
        session.close()


def test_battle_repo_add_record_and_list_by_character():
    session = _build_session()
    try:
        char = UserCharacter(char_config_id=1001, version="v1.0")
        session.add(char)
        session.flush()

        battle_repo = BattleRepository(session)
        battle = battle_repo.create_battle(time=1713000000)
        session.flush()

        battle_repo.add_record(
            battle_id=battle.id,
            user_character_id=char.id,
            record_data={"result": "win"},
        )
        session.commit()

        battles = battle_repo.list_by_character(char.id)
        records = battle_repo.list_records(battle.id)

        assert len(battles) == 1
        assert battles[0].id == battle.id
        assert len(records) == 1
        assert records[0].record_data["result"] == "win"
    finally:
        session.close()
