from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.db.user_team import UserTeam


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return Session(engine)


def test_user_team_user_character_many_to_many_bidirectional_query():
    session = _build_session()

    try:
        character = UserCharacter(char_config_id=1001, version="v1.0")
        team = UserTeam(team_name="Seele Team")
        team.characters.append(character)

        session.add(team)
        session.commit()

        fetched_team = session.get(UserTeam, team.id)
        fetched_character = session.get(UserCharacter, character.id)

        assert fetched_team is not None
        assert fetched_character is not None
        assert len(fetched_team.characters) == 1
        assert fetched_team.characters[0].id == character.id
        assert len(fetched_character.teams) == 1
        assert fetched_character.teams[0].id == team.id
    finally:
        session.close()
