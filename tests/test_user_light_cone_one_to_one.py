import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.db.user_light_cones import UserLightCone


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_user_character_equipped_light_cone_unique_constraint():
    session = _build_session()

    try:
        character_1 = UserCharacter(
            char_config_id=1001,
            version="v1.0",
            level=80,
            eidolon_level=0,
        )
        character_2 = UserCharacter(
            char_config_id=1002,
            version="v1.0",
            level=80,
            eidolon_level=0,
        )
        session.add_all([character_1, character_2])
        session.flush()

        light_cone = UserLightCone(config_id=2001, version="v1.0")
        session.add(light_cone)
        session.flush()

        character_1.equipped_light_cone_id = light_cone.id
        character_2.equipped_light_cone_id = light_cone.id

        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_character_light_cone_relationship_is_scalar():
    session = _build_session()

    try:
        character = UserCharacter(
            char_config_id=1002,
            version="v1.0",
            level=80,
            eidolon_level=0,
        )
        session.add(character)
        session.flush()

        light_cone = UserLightCone(config_id=3001, version="v1.0", character=character)
        session.add(light_cone)
        session.commit()

        fetched_character = session.get(UserCharacter, character.id)
        assert fetched_character is not None
        assert fetched_character.equipped_light_cone is not None
        assert fetched_character.equipped_light_cone.id == light_cone.id
    finally:
        session.close()
