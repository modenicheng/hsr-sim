from unittest.mock import MagicMock

from hsr_sim.models.db.user_light_cones import UserLightCone
from hsr_sim.repositories.light_cone_repo import LightConeRepository


def test_light_cone_repo_model_is_user_light_cone():
    mock_db = MagicMock()
    repo = LightConeRepository(mock_db)
    assert repo.model is UserLightCone


def test_light_cone_repo_initializes_with_db():
    mock_db = MagicMock()
    repo = LightConeRepository(mock_db)
    assert repo.db is mock_db
