from hsr_sim.models.db.user_relics import UserRelic
from .base import BaseRepository

class RelicRepository(BaseRepository[UserRelic]):

    def __init__(self, db):
        super().__init__(UserRelic, db)
