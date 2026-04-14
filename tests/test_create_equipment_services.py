import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.repositories.light_cone_repo import LightConeRepository
from hsr_sim.repositories.relic_repo import RelicRepository
from hsr_sim.services.create_light_cones import LightConeService
from hsr_sim.services.create_relics import RelicService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_relic_service_create_relic_persists():
    session = _build_session()
    try:
        service = RelicService(RelicRepository(session))
        relic = service.create_relic(
            set_id=21000001,
            slot="head",
            main_stat_type="hp_flat",
            level=3,
            rarity=5,
            sub_stats=[{"type": "atk_percent", "roll": 2}],
        )

        assert relic.id is not None
        fetched = session.get(type(relic), relic.id)
        assert fetched is not None
        assert fetched.set_id == 21000001
        assert fetched.slot == "head"
        assert fetched.main_stat_type == "hp_flat"
    finally:
        session.close()


def test_light_cone_service_create_light_cone_persists():
    session = _build_session()
    try:
        service = LightConeService(LightConeRepository(session))
        light_cone = service.create_light_cone(config_id=30000001, level=70)

        assert light_cone.id is not None
        fetched = session.get(type(light_cone), light_cone.id)
        assert fetched is not None
        assert fetched.config_id == 30000001
        assert fetched.level == 70
    finally:
        session.close()


def test_light_cone_service_create_and_equip_to_character():
    session = _build_session()
    try:
        character = UserCharacter(char_config_id=10000001, version="v1.0")
        session.add(character)
        session.commit()

        service = LightConeService(LightConeRepository(session))
        light_cone = service.create_light_cone(
            config_id=30000002,
            equipped_to_character_id=character.id,
        )

        fetched_character = session.get(UserCharacter, character.id)
        assert fetched_character is not None
        assert fetched_character.equipped_light_cone_id == light_cone.id
    finally:
        session.close()


def test_light_cone_service_raises_when_character_not_found():
    session = _build_session()
    try:
        service = LightConeService(LightConeRepository(session))
        with pytest.raises(ValueError):
            service.create_light_cone(
                config_id=30000003,
                equipped_to_character_id=999999,
            )
    finally:
        session.close()
