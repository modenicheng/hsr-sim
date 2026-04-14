import pytest
from unittest.mock import MagicMock

from hsr_sim.utils.db_session import get_db, SessionLocal, engine


def test_session_local_is_sessionmaker():
    from sqlalchemy.orm import sessionmaker

    assert isinstance(SessionLocal, sessionmaker)


def test_engine_is_engine():
    from sqlalchemy import Engine

    assert isinstance(engine, Engine)


def test_get_db_is_generator():
    gen = get_db()
    assert hasattr(gen, "__next__")


def test_get_db_yields_session():
    gen = get_db()
    session = next(gen)
    assert session is not None


def test_get_db_closes_on_stopiteration():
    gen = get_db()
    db = next(gen)
    db.close = MagicMock()
    with pytest.raises(StopIteration):
        gen.send(None)
    db.close.assert_called_once()
