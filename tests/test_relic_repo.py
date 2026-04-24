from unittest.mock import MagicMock

from hsr_sim.repositories.relic_repo import RelicRepository
from hsr_sim.models.db.user_relics import UserRelic


def test_relic_repo_inherits_base_repository():
    assert issubclass(RelicRepository, object)


def test_relic_repo_model_is_user_relic():
    mock_db = MagicMock()
    repo = RelicRepository(mock_db)
    assert repo.model is UserRelic


def test_relic_repo_initializes_with_db():
    mock_db = MagicMock()
    repo = RelicRepository(mock_db)
    assert repo.db is mock_db
