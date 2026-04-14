import pytest
from unittest.mock import MagicMock, patch

from hsr_sim.repositories.base import BaseRepository


class DummyModel:
    pass


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return BaseRepository(DummyModel, mock_db)


class TestBaseRepository:
    def test_get_returns_object(self, repo, mock_db):
        mock_obj = MagicMock()
        mock_db.get.return_value = mock_obj

        result = repo.get(1)

        mock_db.get.assert_called_once_with(DummyModel, 1)
        assert result is mock_obj

    def test_get_returns_none_when_not_found(self, repo, mock_db):
        mock_db.get.return_value = None

        result = repo.get(999)

        assert result is None

    def test_get_all_returns_all(self, repo, mock_db):
        mock_objs = [MagicMock(), MagicMock()]
        mock_db.query.return_value.all.return_value = mock_objs

        result = repo.get_all()

        mock_db.query.assert_called_once_with(DummyModel)
        mock_db.query.return_value.all.assert_called_once()
        assert result == mock_objs

    def test_add_adds_and_returns_object(self, repo, mock_db):
        mock_obj = MagicMock()

        result = repo.add(mock_obj)

        mock_db.add.assert_called_once_with(mock_obj)
        assert result is mock_obj

    def test_add_all_adds_all_returns_list(self, repo, mock_db):
        mock_objs = [MagicMock(), MagicMock()]

        result = repo.add_all(mock_objs)

        mock_db.add_all.assert_called_once_with(mock_objs)
        assert result == mock_objs

    def test_delete_existing_object(self, repo, mock_db):
        mock_obj = MagicMock()
        mock_db.get.return_value = mock_obj

        repo.delete(1)

        mock_db.get.assert_called_once_with(DummyModel, 1)
        mock_db.delete.assert_called_once_with(mock_obj)

    def test_delete_nonexistent_logs_warning(self, repo, mock_db):
        from hsr_sim.repositories.base import logger

        mock_db.get.return_value = None

        with patch.object(logger, "warning") as mock_warn:
            repo.delete(999)
            mock_warn.assert_called_once()
