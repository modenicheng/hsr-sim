import random

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from hsr_sim.models.db.base import Base
from hsr_sim.models.schemas.enums import RelicSlot
from hsr_sim.repositories.relic_repo import RelicRepository
from hsr_sim.services.relic_generator import RelicGenerator


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_relic_generator_generates_and_persists_relic():
    session = _build_session()
    try:
        generator = RelicGenerator(
            relic_repo=RelicRepository(session),
            rng=random.Random(42),
        )

        relic = generator.generate(
            set_id=21000001,
            slot=RelicSlot.TORSO,
            rarity=5,
            level=0,
            main_stat_type="crit_rate",
            sub_stat_count=4,
        )

        assert relic.id is not None
        assert relic.main_stat_type == "crit_rate"
        assert relic.slot == "torso"
        assert len(relic.sub_stats) == 4

        sub_stat_types = {sub["type"] for sub in relic.sub_stats}
        assert "crit_rate" not in sub_stat_types
        assert len(sub_stat_types) == 4

        fetched = session.get(type(relic), relic.id)
        assert fetched is not None
        assert fetched.set_id == 21000001
    finally:
        session.close()


def test_relic_generator_rejects_invalid_main_stat_for_slot():
    session = _build_session()
    try:
        generator = RelicGenerator(
            relic_repo=RelicRepository(session),
            rng=random.Random(7),
        )

        try:
            generator.generate(
                set_id=21000002,
                slot=RelicSlot.HEAD,
                main_stat_type="crit_rate",
            )
        except ValueError as exc:
            assert "Invalid main stat" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid main stat")
    finally:
        session.close()
