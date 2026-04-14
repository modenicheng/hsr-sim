import pytest
import uuid

from hsr_sim.utils.id_generator import new_id


def test_new_id_returns_valid_uuid():
    result = new_id()
    assert isinstance(result, str)
    uuid.UUID(result)


def test_new_id_returns_unique_values():
    ids = [new_id() for _ in range(100)]
    assert len(set(ids)) == 100
